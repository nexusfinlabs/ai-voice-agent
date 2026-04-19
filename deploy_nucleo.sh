#!/bin/bash
# deploy_nucleo.sh — despliega todos los cambios de hoy al TSC
# Ejecutar desde Mac: bash deploy_nucleo.sh
# Requiere: ssh tsc configurado en ~/.ssh/config

set -e
REPO=/Users/alberto/Desktop/SW_AI/ai-agents
TSC_HOST=tsc

echo ""
echo "=== 1. Gateway v2 ==="
scp $REPO/agents_voice/nucleo/gateway_v2.js \
    $TSC_HOST:/home/tsc/app/wa-gateway/gateway.js

scp $REPO/agents_voice/nucleo/gateway.env \
    $TSC_HOST:/home/tsc/app/wa-gateway/.env

ssh $TSC_HOST "systemctl --user restart tsc-wa-gateway && sleep 2 && systemctl --user status tsc-wa-gateway --no-pager | head -8"

echo ""
echo "=== 2. Nucleo app.py + properties.py ==="
ssh $TSC_HOST "mkdir -p /home/tsc/app/nucleo"
scp $REPO/agents_voice/nucleo/app.py         $TSC_HOST:/home/tsc/app/nucleo/
scp $REPO/agents_voice/nucleo/properties.py  $TSC_HOST:/home/tsc/app/nucleo/
scp $REPO/agents_voice/nucleo/leads_storage.py $TSC_HOST:/home/tsc/app/nucleo/
scp $REPO/agents_voice/nucleo/.env           $TSC_HOST:/home/tsc/app/nucleo/
# Nota: asegurate de tener SUPABASE_KEY (service_role) en el .env antes de copiar

# Instalar anthropic si no está
ssh $TSC_HOST "cd /home/tsc/app/nucleo && source venv/bin/activate 2>/dev/null || python3 -m venv venv && venv/bin/pip install -q anthropic supabase fastapi uvicorn python-dotenv"

# Reiniciar servicio nucleo (si existe, si no crearlo)
ssh $TSC_HOST "systemctl --user restart tsc-nucleo-agent 2>/dev/null || echo 'Servicio tsc-nucleo-agent no encontrado — crear con systemd'"

echo ""
echo "=== 3. BB4x4 fix (deshabilitar OpenClaw double-send) ==="
scp $REPO/agents/bb4x4/app/api/routes_whatsapp.py \
    $TSC_HOST:/home/tsc/app/bb4x4_agent/app/api/routes_whatsapp.py
ssh $TSC_HOST "systemctl --user restart tsc-bb4x4-agent && sleep 2 && systemctl --user status tsc-bb4x4-agent --no-pager | head -6"

echo ""
echo "=== 4. Next.js web — rebuild ==="
scp $REPO/agents_voice/nucleo/web/src/app/page.tsx \
    $TSC_HOST:/home/tsc/app/nucleo-web/src/app/page.tsx 2>/dev/null || echo "Directorio nucleo-web no encontrado en TSC — hacer deploy manual"

echo ""
echo "=== Verificar routing gateway ==="
curl -s http://localhost:8005/api/routing 2>/dev/null || \
  ssh $TSC_HOST "curl -s http://localhost:8005/api/routing" | python3 -m json.tool

echo ""
echo "✅ Deploy completado"
echo ""
echo "Test WhatsApp:"
echo "  Escribe 'INMO Hola' a +34663103334"
echo "  Escribe 'BB4X4 Hi, I am interested in...' a +34663103334"
echo "  Escribe 'RESTAURANTE Quiero reservar' a +34663103334"
