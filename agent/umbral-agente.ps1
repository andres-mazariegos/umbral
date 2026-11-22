<#
  Agente de Umbral para Windows (PowerShell)
  ==========================================
  Hace lo mismo que umbral_agente.py, pero no necesita instalar Python:
  PowerShell ya viene en Windows 10 y 11.

  Te pide permiso, mira qué puertas (puertos) tiene abiertas esta computadora
  y manda esa lista a tu cuenta de Umbral para que te la explique.

  SÍ lee:  número de puerto, protocolo, dirección donde escucha, nombre y
           carpeta del programa que lo abrió, versión de Windows y si el
           cortafuegos está encendido.
  NO lee:  archivos, contraseñas, historial, fotos, teclas, pantalla ni el
           contenido de lo que viaja por la red. Tampoco cambia nada.

  Uso (desde la carpeta donde lo descargaste):
    powershell -ExecutionPolicy Bypass -File .\umbral-agente.ps1 -Servidor https://tu-sitio -Codigo K7QM-2XRD
    powershell -ExecutionPolicy Bypass -File .\umbral-agente.ps1            (siguientes veces)
    powershell -ExecutionPolicy Bypass -File .\umbral-agente.ps1 -Ver       (solo muestra, no envía)
    powershell -ExecutionPolicy Bypass -File .\umbral-agente.ps1 -Vigilar 30
    powershell -ExecutionPolicy Bypass -File .\umbral-agente.ps1 -Olvidar

  "-ExecutionPolicy Bypass" solo aplica a esta ejecución: no cambia la
  configuración de seguridad de tu Windows.
#>
param(
    [string]$Servidor = "",
    [string]$Codigo = "",
    [switch]$Ver,
    [int]$Vigilar = 0,
    [switch]$Olvidar
)

$VERSION = "1.0-ps"
$CARPETA = Join-Path $HOME ".umbral"
$ARCHIVO = Join-Path $CARPETA "agente.json"   # el mismo archivo que usa el agente de Python
$MAX_PUERTOS = 400

# Windows PowerShell 5.1 a veces no activa TLS 1.2 por su cuenta.
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch { }

# ----------------------------------------------------------- utilidades

function Escribir-Titulo([string]$texto) {
    Write-Host ""
    Write-Host $texto
    Write-Host ("-" * $texto.Length)
}

function Quitar-Usuario([string]$ruta) {
    # C:\Users\ana\app.exe  ->  ~\app.exe  (tu nombre de usuario no sale de tu equipo)
    if (-not $ruta) { return "" }
    $casa = $HOME
    if ($casa -and $ruta.ToLower().StartsWith($casa.ToLower())) { $ruta = "~" + $ruta.Substring($casa.Length) }
    if ($ruta.Length -gt 260) { $ruta = $ruta.Substring(0, 260) }
    return $ruta
}

function Detalle-Sistema {
    try {
        $so = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        $texto = "$($so.Caption) $($so.Version)".Trim()
    } catch {
        $texto = "Windows " + [Environment]::OSVersion.Version.ToString()
    }
    if ($texto.Length -gt 120) { $texto = $texto.Substring(0, 120) }
    return $texto
}

function Estado-Cortafuegos {
    try {
        $perfiles = @(Get-NetFirewallProfile -ErrorAction Stop)
        if ($perfiles.Count -eq 0) { return "desconocido" }
        foreach ($p in $perfiles) {
            if ("$($p.Enabled)" -notin @("True", "1")) { return "apagado" }
        }
        return "activo"
    } catch {
        return "desconocido"
    }
}

# ----------------------------------------------------------- recolección

function Recolectar {
    # Nombre y ruta de cada programa, por número de proceso.
    $programas = @{}
    foreach ($proc in @(Get-Process -ErrorAction SilentlyContinue)) {
        $ruta = ""
        try { $ruta = [string]$proc.Path } catch { $ruta = "" }
        $programas[[int]$proc.Id] = @{ nombre = [string]$proc.ProcessName; ruta = $ruta }
    }

    $crudos = New-Object System.Collections.ArrayList
    foreach ($c in @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue)) {
        [void]$crudos.Add(@{ puerto = [int]$c.LocalPort; protocolo = "tcp"; direccion = [string]$c.LocalAddress; pid = [int]$c.OwningProcess })
    }
    foreach ($u in @(Get-NetUDPEndpoint -ErrorAction SilentlyContinue)) {
        if ([int]$u.LocalPort -gt 0) {
            [void]$crudos.Add(@{ puerto = [int]$u.LocalPort; protocolo = "udp"; direccion = [string]$u.LocalAddress; pid = [int]$u.OwningProcess })
        }
    }

    $vistos = @{}
    $puertos = New-Object System.Collections.ArrayList
    foreach ($p in ($crudos | Sort-Object { $_.puerto }, { $_.protocolo }, { $_.direccion })) {
        $direccion = ($p.direccion -split "%")[0]
        if ($direccion -eq "") { $direccion = "0.0.0.0" }
        $clave = "$($p.puerto)/$($p.protocolo)/$direccion"
        if ($vistos.ContainsKey($clave)) { continue }
        $vistos[$clave] = $true
        $nombre = ""; $ruta = ""
        if ($programas.ContainsKey($p.pid)) { $nombre = $programas[$p.pid].nombre; $ruta = $programas[$p.pid].ruta }
        if ($nombre -and -not $nombre.ToLower().EndsWith(".exe") -and $nombre -notin @("System", "Idle")) { $nombre = "$nombre.exe" }
        if ($nombre.Length -gt 80) { $nombre = $nombre.Substring(0, 80) }
        [void]$puertos.Add([ordered]@{
            puerto = $p.puerto; protocolo = $p.protocolo; direccion = $direccion
            proceso = $nombre; ruta = (Quitar-Usuario $ruta)
        })
        if ($puertos.Count -ge $MAX_PUERTOS) { break }
    }

    return [ordered]@{
        version_agente  = $VERSION
        metodo          = "powershell"
        sistema         = "windows"
        detalle_sistema = (Detalle-Sistema)
        cortafuegos     = (Estado-Cortafuegos)
        puertos         = $puertos
    }
}

# ----------------------------------------------------------- red

function Direccion-Valida([string]$servidor) {
    # Solo http:// o https:// (nada de file:// ni otras rutas raras).
    $uri = $null
    if (-not [Uri]::TryCreate($servidor, [UriKind]::Absolute, [ref]$uri)) { return $false }
    return ($uri.Scheme -in @("http", "https")) -and $uri.Host
}

function Pedir([string]$servidor, [string]$ruta, $datos, [string]$llave = "") {
    if (-not (Direccion-Valida $servidor)) {
        return @{ estado = 0; cuerpo = @{ detail = "La dirección «$servidor» no es válida. Debe empezar con http:// o https://" } }
    }
    $cabeceras = @{ "User-Agent" = "umbral-agente/$VERSION" }
    if ($llave) { $cabeceras["Authorization"] = "Bearer $llave" }
    $json = $datos | ConvertTo-Json -Depth 6 -Compress
    $bytes = [Text.Encoding]::UTF8.GetBytes($json)
    try {
        $r = Invoke-WebRequest -Uri ($servidor.TrimEnd("/") + $ruta) -Method Post -Body $bytes `
             -ContentType "application/json; charset=utf-8" -Headers $cabeceras -UseBasicParsing -TimeoutSec 25
        $texto = $r.Content
        if ($texto -is [byte[]]) { $texto = [Text.Encoding]::UTF8.GetString($texto) }
        $cuerpo = @{}
        if ($texto) { $cuerpo = $texto | ConvertFrom-Json }
        return @{ estado = [int]$r.StatusCode; cuerpo = $cuerpo }
    } catch {
        $estado = 0
        $detalle = "No se pudo llegar a $servidor. ¿Escribiste bien la dirección y tienes internet?"
        if ($_.Exception.Response) {
            try { $estado = [int]$_.Exception.Response.StatusCode } catch { $estado = 0 }
            $detalle = "Error $estado del servidor."
            if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
                try { $detalle = ($_.ErrorDetails.Message | ConvertFrom-Json).detail } catch { }
            }
        }
        return @{ estado = $estado; cuerpo = @{ detail = $detalle } }
    }
}

function Cargar-Conexion {
    if (-not (Test-Path $ARCHIVO)) { return $null }
    try { return (Get-Content $ARCHIVO -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { return $null }
}

function Guardar-Conexion($datos) {
    if (-not (Test-Path $CARPETA)) { New-Item -ItemType Directory -Path $CARPETA | Out-Null }
    ($datos | ConvertTo-Json) | Set-Content -Path $ARCHIVO -Encoding UTF8
    # Solo tu usuario puede leer la llave de este equipo.
    try { & icacls $ARCHIVO /inheritance:r /grant:r "$($env:USERNAME):(R,W)" | Out-Null } catch { }
}

# ----------------------------------------------------------- pantalla

function Mostrar($reporte) {
    Escribir-Titulo "Esto es lo que encontró el agente"
    Write-Host ("  Sistema:      " + $reporte.detalle_sistema)
    Write-Host ("  Cortafuegos:  " + $reporte.cortafuegos)
    Write-Host ("  Puertas abiertas: " + $reporte.puertos.Count)
    Write-Host ""
    Write-Host ("  {0,-8}{1,-6}{2,-26}{3}" -f "PUERTO", "TIPO", "ESCUCHA EN", "PROGRAMA")
    $ocultos = $false
    foreach ($p in $reporte.puertos) {
        $programa = $p.proceso
        if (-not $programa) { $programa = "(no visible)"; $ocultos = $true }
        $dir = $p.direccion; if ($dir.Length -gt 24) { $dir = $dir.Substring(0, 24) }
        Write-Host ("  {0,-8}{1,-6}{2,-26}{3}" -f $p.puerto, $p.protocolo, $dir, $programa)
    }
    if ($ocultos) {
        Write-Host ""
        Write-Host "  Hay programas que no se pudieron ver. Para verlos todos abre PowerShell con clic derecho > Ejecutar como administrador."
    }
}

function Pedir-Permiso {
    Escribir-Titulo "Umbral necesita tu permiso"
    Write-Host "  Voy a revisar qué puertas (puertos) tiene abiertas esta computadora"
    Write-Host "  y a enviar esa lista a tu cuenta de Umbral para explicártela."
    Write-Host ""
    Write-Host "  SÍ leo:  número de puerto, programa que lo abrió, sistema y cortafuegos."
    Write-Host "  NO leo:  archivos, contraseñas, historial, fotos ni lo que escribes."
    Write-Host "  NO cambio nada en tu equipo."
    Write-Host ""
    $r = (Read-Host "  ¿Me das permiso para revisar ahora? (s/n)").Trim().ToLower()
    return $r -in @("s", "si", "sí", "y", "yes")
}

function Conectar($guardado) {
    Escribir-Titulo "Conectar este equipo con tu cuenta"
    $servidor = $Servidor
    if (-not $servidor -and $guardado) { $servidor = $guardado.servidor }
    if (-not $servidor) { $servidor = (Read-Host "  Dirección de Umbral (ej. https://umbral.mazariegoscarlos.com)").Trim() }
    if ($servidor -notmatch "^https?://") { $servidor = "https://" + $servidor }
    $codigo = $Codigo
    if (-not $codigo) { $codigo = Read-Host "  Código que te muestra Umbral (ej. K7QM-2XRD)" }
    $codigo = $codigo.Trim().ToUpper()

    $r = Pedir $servidor "/api/agente/enlazar" @{ codigo = $codigo; sistema = "windows"; detalle_sistema = (Detalle-Sistema) }
    if ($r.estado -ne 200) {
        Write-Host ""
        Write-Host ("  No se pudo conectar: " + $r.cuerpo.detail)
        return $null
    }
    $datos = [ordered]@{ servidor = $servidor; llave = $r.cuerpo.llave; equipo = $r.cuerpo.equipo }
    Guardar-Conexion $datos
    Write-Host ""
    Write-Host "  Listo. Este equipo quedó conectado como «$($datos.equipo)»."
    return $datos
}

function Revisar-Y-Enviar($datos) {
    Write-Host ""
    Write-Host "  Revisando..."
    $reporte = Recolectar
    Mostrar $reporte
    $r = Pedir $datos.servidor "/api/agente/revisiones" $reporte $datos.llave
    if ($r.estado -eq 200) {
        $res = $r.cuerpo.resumen
        Escribir-Titulo "Enviado a Umbral"
        Write-Host ("  Atiéndelo ya: {0}   Ojo aquí: {1}   Tranquilo: {2}" -f $res.urgente, $res.atento, $res.tranquilo)
        Write-Host "  Abre Umbral en tu navegador para leer qué significa cada una."
        return $true
    }
    Write-Host ""
    if ($r.estado -eq 401) {
        Write-Host "  Este equipo fue desconectado desde Umbral. Corre el agente con -Olvidar y vuelve a conectarlo."
    } else {
        Write-Host ("  No se pudo enviar: " + $r.cuerpo.detail)
    }
    return $false
}

# ----------------------------------------------------------- inicio

Write-Host ""
Write-Host "  umbral_  agente $VERSION"

if ($Olvidar) {
    if (Test-Path $ARCHIVO) { Remove-Item $ARCHIVO -Force }
    Write-Host "  Se borró la conexión de este equipo. Para quitarlo de tu cuenta, entra a Umbral > Equipos."
    exit 0
}

if ($Ver) {
    $reporte = Recolectar
    Mostrar $reporte
    Escribir-Titulo "Esto es, tal cual, lo que se enviaría"
    Write-Host ($reporte | ConvertTo-Json -Depth 6)
    exit 0
}

$datos = Cargar-Conexion
if (-not $datos -or -not $datos.llave -or $Codigo) {
    $datos = Conectar $datos
    if (-not $datos) { exit 1 }
}

if (-not (Pedir-Permiso)) {
    Write-Host ""
    Write-Host "  Sin permiso no reviso nada. No se envió ningún dato."
    exit 0
}

if ($Vigilar -le 0) {
    if (Revisar-Y-Enviar $datos) { exit 0 } else { exit 1 }
}

$minutos = [Math]::Max(5, $Vigilar)
Write-Host ""
Write-Host "  Modo vigilancia: revisaré cada $minutos minutos. Para detenerme pulsa Ctrl + C."
while ($true) {
    [void](Revisar-Y-Enviar $datos)
    Start-Sleep -Seconds ($minutos * 60)
}
