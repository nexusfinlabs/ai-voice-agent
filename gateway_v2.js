/**
 * wa-gateway/gateway.js  — v2.0  (multi-tenant)
 * ─────────────────────────────────────────────
 * Número: +34663103334
 *
 * FLUJO:
 *   recibe WA msg → detecta tenant (prefix | sesión | menú) →
 *   reenvía al microservicio correcto → envía UNA sola respuesta via Baileys
 *
 * SESIONES (in-memory, TTL 24h):
 *   Primer mensaje con prefix → sesión fijada al tenant
 *   Mensajes posteriores van al mismo tenant sin prefix
 *   Sin prefix ni sesión → menú de bienvenida
 *
 * ROUTING TABLE:
 *   Cargada desde Supabase (businesses.wa_prefix / wa_service_url / wa_enabled)
 *   Fallback local si Supabase no responde al arrancar
 *
 * OUTBOUND API (puerto GATEWAY_PORT, defecto 8005):
 *   POST /api/send          { target, message }  → enviar mensaje saliente
 *   GET  /api/routing        → ver tabla activa + sesiones abiertas
 *   POST /api/routing/reload → recargar desde Supabase sin reiniciar
 */

'use strict';

const {
  default: makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
} = require('@whiskeysockets/baileys');
const qrcode  = require('qrcode-terminal');
const axios   = require('axios');
const express = require('express');
const path    = require('path');

// ── Config ────────────────────────────────────────────────────────────────────
const SUPABASE_URL   = process.env.SUPABASE_URL      || 'https://lrtmrwsadvnchjqbeeai.supabase.co';
const SUPABASE_KEY   = process.env.SUPABASE_ANON_KEY || '';
const AUTH_FOLDER    = process.env.AUTH_FOLDER       || path.join(__dirname, 'auth_info');
const GATEWAY_PORT   = parseInt(process.env.GATEWAY_PORT || '8005', 10);
const SESSION_TTL_MS = 24 * 60 * 60 * 1000;

// ── Routing fallback (si Supabase no responde al arrancar) ────────────────────
const ROUTING_FALLBACK = {
  'BB4X4':       { slug: 'bb4x4',       url: 'http://127.0.0.1:5064/webhooks/whatsapp/inbound' },
  'RESTAURANTE': { slug: 'restaurants', url: 'http://127.0.0.1:5057/whatsapp/inbound'           },
  'INMO':        { slug: 'nucleo',      url: 'http://127.0.0.1:5065/whatsapp/inbound'            },
};

const WELCOME_MSG =
  '👋 Hola! Soy NexusBot.\n\n' +
  '¿Con quién quieres hablar?\n\n' +
  '🏠 Escribe *INMO* — Inmobiliaria Núcleo (El Campello)\n' +
  '🚙 Escribe *BB4X4* — BlackBox 4x4\n' +
  '🍽️ Escribe *RESTAURANTE* — Nexus Lounge\n\n' +
  'Después del primer mensaje ya no necesitas escribirlo de nuevo.';

// ── Logger ────────────────────────────────────────────────────────────────────
const ts  = () => new Date().toISOString();
const log = {
  info:  (...a) => console.log('[INFO]', ts(), ...a),
  warn:  (...a) => console.log('[WARN]', ts(), ...a),
  error: (...a) => console.error('[ERR]', ts(), ...a),
};

// ── Routing table (cargada en runtime) ───────────────────────────────────────
// prefix.toUpperCase() → { slug, url }
let routingTable = { ...ROUTING_FALLBACK };

async function loadRoutingTable() {
  if (!SUPABASE_KEY) {
    log.warn('SUPABASE_ANON_KEY not set — using fallback routing table');
    return;
  }
  try {
    const res = await axios.get(
      `${SUPABASE_URL}/rest/v1/businesses?wa_enabled=eq.true&select=wa_prefix,wa_service_url,slug`,
      {
        headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}` },
        timeout: 8000,
      }
    );
    const rows = res.data || [];
    if (!rows.length) { log.warn('No wa_enabled rows in Supabase — using fallback'); return; }
    const tbl = {};
    for (const r of rows) {
      if (r.wa_prefix && r.wa_service_url) {
        tbl[r.wa_prefix.trim().toUpperCase()] = { slug: r.slug, url: r.wa_service_url };
      }
    }
    routingTable = tbl;
    log.info('Routing table from Supabase: %s', Object.keys(tbl).join(', '));
  } catch (err) {
    log.warn('Supabase routing load failed (%s) — using fallback', err.message);
  }
}

// ── Session store (in-memory, TTL 24h) ───────────────────────────────────────
const sessions = new Map(); // senderId → { slug, url, prefix, lastAt }

function getSession(sender) {
  const s = sessions.get(sender);
  if (!s) return null;
  if (Date.now() - s.lastAt > SESSION_TTL_MS) { sessions.delete(sender); return null; }
  return s;
}
function setSession(sender, route, prefix) {
  sessions.set(sender, { ...route, prefix, lastAt: Date.now() });
}
function touchSession(sender) {
  const s = sessions.get(sender);
  if (s) s.lastAt = Date.now();
}

// ── Router ────────────────────────────────────────────────────────────────────
// Devuelve { route: {slug, url}, cleanBody } o null
function resolveRoute(sender, rawBody) {
  const body      = rawBody.trim();
  const firstWord = body.split(/[\s:]/)[0].toUpperCase().replace(/[^A-Z0-9]/g, '');

  // 1. Prefix detectado en el mensaje
  const byPrefix = routingTable[firstWord];
  if (byPrefix) {
    setSession(sender, byPrefix, firstWord);
    // Quitar el prefix + separador del cuerpo
    const cleanBody = body.replace(/^[^\s:]+[\s:]*/u, '').trim() || body;
    log.info('PREFIX "%s" → %s | clean: "%s"', firstWord, byPrefix.slug, cleanBody.slice(0, 60));
    return { route: byPrefix, cleanBody };
  }

  // 2. Sesión activa
  const session = getSession(sender);
  if (session) {
    touchSession(sender);
    log.info('SESSION → %s', session.slug);
    return { route: { slug: session.slug, url: session.url }, cleanBody: body };
  }

  // 3. Sin match
  return null;
}

// ── Forward a microservicio ───────────────────────────────────────────────────
async function forwardToService(url, payload) {
  const res = await axios.post(url, payload, { timeout: 45000 });
  const reply  = (res.data?.reply  || '').trim();
  const status = (res.data?.status || 'ok');
  return { reply, status };
}

// ── API server outbound ───────────────────────────────────────────────────────
function startApiServer(sock) {
  const app = express();
  app.use(express.json());

  // POST /api/send  → { target, message }
  app.post('/api/send', async (req, res) => {
    const { target, message } = req.body || {};
    if (!target || !message) return res.status(400).json({ error: 'target and message required' });
    try {
      const jid = target.includes('@') ? target : `${target.replace('+', '')}@s.whatsapp.net`;
      await sock.sendMessage(jid, { text: message });
      log.info('API OUT → %s (%d chars)', jid, message.length);
      res.json({ success: true });
    } catch (err) {
      log.error('API send error: %s', err.message);
      res.status(500).json({ error: err.message });
    }
  });

  // GET /api/routing → debug tabla activa
  app.get('/api/routing', (_req, res) => {
    res.json({
      table:    routingTable,
      sessions: sessions.size,
      tenants:  [...sessions.entries()].map(([k, v]) => ({ sender: `***${k.slice(-4)}`, slug: v.slug })),
    });
  });

  // POST /api/routing/reload → recarga Supabase sin reiniciar
  app.post('/api/routing/reload', async (_req, res) => {
    await loadRoutingTable();
    res.json({ table: routingTable });
  });

  app.listen(GATEWAY_PORT, '127.0.0.1', () =>
    log.info('Gateway API on 127.0.0.1:%d', GATEWAY_PORT)
  );
}

// ── WhatsApp Connection ───────────────────────────────────────────────────────
async function connectToWhatsApp() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);
  const { version }          = await fetchLatestBaileysVersion();

  log.info('Baileys %s | Tenants: %s', version.join('.'), Object.keys(routingTable).join(', '));

  const sock = makeWASocket({
    version,
    auth:                      state,
    printQRInTerminal:         false,
    logger:                    require('pino')({ level: 'silent' }),
    getMessage:                async () => undefined,
    generateHighQualityLinkPreview: false,
    syncFullHistory:           false,
  });

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', ({ connection, lastDisconnect, qr }) => {
    if (qr) {
      console.log('\n🔷 ESCANEA ESTE QR CON +34663103334');
      console.log('   Settings → Linked Devices → Link a Device\n');
      qrcode.generate(qr, { small: true });
    }
    if (connection === 'close') {
      const code      = lastDisconnect?.error?.output?.statusCode;
      const loggedOut = code === DisconnectReason.loggedOut;
      log.warn('Closed (code=%d, loggedOut=%s)', code, loggedOut);
      if (!loggedOut) { log.info('Reconnecting…'); connectToWhatsApp(); }
      else { log.error('Logged out — delete auth_info/ and restart.'); process.exit(1); }
    } else if (connection === 'open') {
      log.info('✅ WhatsApp CONNECTED +34663103334 | Routing: %s', Object.keys(routingTable).join(', '));
    }
  });

  // ── Incoming messages ───────────────────────────────────────────────────────
  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    if (type !== 'notify') return;

    for (const msg of messages) {
      if (msg.key.fromMe)                         continue;
      if (msg.key.remoteJid === 'status@broadcast') continue;

      const rawSender  = msg.key.participant || msg.key.remoteJid || '';
      const jid        = msg.key.remoteJid || rawSender;
      const senderId   = rawSender.replace(/@s\.whatsapp\.net|@g\.us|@lid/g, '');
      const senderType = rawSender.includes('@lid') ? 'lid' : 'phone';
      const pushName   = (msg.pushName || '').trim();
      const phoneE164  = senderType === 'phone' && /^\d{6,20}$/.test(senderId) ? `+${senderId}` : null;

      const body =
        msg.message?.conversation ||
        msg.message?.extendedTextMessage?.text ||
        msg.message?.imageMessage?.caption || '';

      if (!body.trim()) continue;

      log.info('IN ***%s [%s]: %s', senderId.slice(-4), senderType, body.slice(0, 80));

      // ── Routing ─────────────────────────────────────────────────────────────
      const resolved = resolveRoute(senderId, body);

      if (!resolved) {
        // Sin prefix ni sesión → menú
        await sock.sendMessage(jid, { text: WELCOME_MSG });
        log.info('WELCOME → ***%s (no route)', senderId.slice(-4));
        continue;
      }

      const { route, cleanBody } = resolved;

      // ── Forward al microservicio ─────────────────────────────────────────────
      try {
        const { reply } = await forwardToService(route.url, {
          sender:     senderId,
          senderId,
          rawJid:     rawSender,
          senderType,
          pushName,
          phoneE164,
          body:       cleanBody,
          channel:    'whatsapp',
          tenant:     route.slug,
        });

        if (reply) {
          await sock.sendMessage(jid, { text: reply });
          log.info('OUT ***%s [%s] %d chars', senderId.slice(-4), route.slug, reply.length);
        } else {
          log.warn('Empty reply from %s for ***%s', route.slug, senderId.slice(-4));
        }
      } catch (err) {
        log.error('Forward error → %s: %s', route.url, err.message);
        await sock.sendMessage(jid, {
          text: '⚠️ Hay un problema técnico. Un momento y lo resolvemos.',
        });
      }
    }
  });

  startApiServer(sock);
}

// ── Boot ─────────────────────────────────────────────────────────────────────
(async () => {
  await loadRoutingTable();
  connectToWhatsApp().catch(err => { console.error('Fatal:', err); process.exit(1); });
})();
