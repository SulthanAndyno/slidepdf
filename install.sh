#!/usr/bin/env bash
# SlidePDF Studio - Linux System Integration Installer
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "   SlidePDF Studio - System Installer   "
echo "========================================="

# 1. Check Python
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo "✕ Error: Python 3 is required but was not found on PATH." >&2
    exit 1
fi
echo "✓ Python detected: $($PYTHON_BIN --version)"

# 2. Setup Virtual Environment if missing
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv..."
    if command -v uv &>/dev/null; then
        uv venv
        uv pip install -r requirements.txt
    else
        $PYTHON_BIN -m venv .venv
        .venv/bin/pip install --upgrade pip
        .venv/bin/pip install -r requirements.txt
    fi
    echo "✓ Virtual environment created and packages installed."
else
    echo "✓ Existing virtual environment found."
fi

# 3. Install Global CLI Command to ~/.local/bin
mkdir -p "$HOME/.local/bin"
LAUNCHER="$HOME/.local/bin/slidepdf"
cat > "$LAUNCHER" << EOF
#!/usr/bin/env bash
# SlidePDF Global CLI / GUI Launcher
PROJECT_DIR="$SCRIPT_DIR"
EXEC="\$PROJECT_DIR/run.sh"

if [ ! -f "\$EXEC" ]; then
    echo "Error: SlidePDF Studio not found at \$EXEC" >&2
    exit 1
fi

if [ \$# -eq 1 ] && [ -f "\$1" ]; then
    EXT="\${1##*.}"
    EXT_LOWER="\$(echo "\$EXT" | tr '[:upper:]' '[:lower:]')"
    case "\$EXT_LOWER" in
        pptx|ppt|pptm|ppsx|pps|potx|pot|odp|png|jpg|jpeg|webp|bmp|tiff|docx|doc|odt)
            echo "⚡ Converting '\$1' to PDF..."
            exec "\$EXEC" convert "\$1"
            ;;
        *)
            exec "\$EXEC" "\$@"
            ;;
    esac
else
    exec "\$EXEC" "\$@"
fi
EOF
chmod +x "$LAUNCHER"
ln -sf "$LAUNCHER" "$HOME/.local/bin/pptx2pdf"
echo "✓ Global CLI installed: slidepdf, pptx2pdf in ~/.local/bin"

# 4. Install Desktop Application Launcher (.desktop)
mkdir -p "$HOME/.local/share/applications"
DESKTOP_FILE="$HOME/.local/share/applications/slidepdf.desktop"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SlidePDF Studio
GenericName=Presentation & Document to PDF Converter
Comment=Modern multi-engine presentation to PDF converter studio
Exec=$SCRIPT_DIR/run.sh %F
Icon=$SCRIPT_DIR/assets/icon.png
Terminal=false
Categories=Office;Utility;Graphics;
Keywords=pptx;pdf;converter;powerpoint;presentation;slides;odp;
MimeType=application/vnd.openxmlformats-officedocument.presentationml.presentation;application/vnd.ms-powerpoint;application/vnd.oasis.opendocument.presentation;
StartupNotify=true
Actions=Doctor;Batch;

[Desktop Action Doctor]
Name=Engine Diagnostics (Doctor)
Exec=$SCRIPT_DIR/run.sh doctor
Terminal=true

[Desktop Action Batch]
Name=Batch Convert Folder
Exec=$SCRIPT_DIR/run.sh batch
Terminal=true
EOF
chmod +x "$DESKTOP_FILE"
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi
echo "✓ Desktop application entry installed to ~/.local/share/applications/slidepdf.desktop"

# 5. Install Nautilus / GNOME Files Right-Click Context Script
NAUTILUS_DIR="$HOME/.local/share/nautilus/scripts"
mkdir -p "$NAUTILUS_DIR"
NAUTILUS_SCRIPT="$NAUTILUS_DIR/Convert to PDF (SlidePDF)"
cat > "$NAUTILUS_SCRIPT" << EOF
#!/usr/bin/env bash
# Nautilus Script for SlidePDF Studio
LOG_FILE="/tmp/slidepdf_nautilus.log"
ICON="$SCRIPT_DIR/assets/icon.png"
APP_EXEC="$HOME/.local/bin/slidepdf"

FILES=()
if [ -n "\$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS" ]; then
    while IFS= read -r line; do
        [ -n "\$line" ] && FILES+=("\$line")
    done <<< "\$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"
fi

if [ \${#FILES[@]} -eq 0 ] && [ \$# -gt 0 ]; then
    for arg in "\$@"; do
        FILES+=("\$arg")
    done
fi

if [ \${#FILES[@]} -eq 0 ]; then
    notify-send -i "\$ICON" "SlidePDF Studio" "Tidak ada berkas yang dipilih." 2>/dev/null || true
    exit 0
fi

COUNT=0
SUPPORTED_EXTS=("pptx" "ppt" "pptm" "ppsx" "pps" "potx" "odp" "png" "jpg" "jpeg" "webp" "bmp" "docx" "doc" "odt")

for RAW_FILE in "\${FILES[@]}"; do
    FILE="\$(realpath "\$RAW_FILE" 2>/dev/null || echo "\$RAW_FILE")"
    EXT="\${FILE##*.}"
    EXT_LOWER="\$(echo "\$EXT" | tr '[:upper:]' '[:lower:]')"

    IS_SUPPORTED=0
    for s_ext in "\${SUPPORTED_EXTS[@]}"; do
        if [ "\$EXT_LOWER" == "\$s_ext" ]; then
            IS_SUPPORTED=1
            break
        fi
    done

    if [[ -f "\$FILE" && \$IS_SUPPORTED -eq 1 ]]; then
        notify-send -i "\$ICON" "SlidePDF Studio" "Sedang mengonversi: \$(basename "\$FILE")..." 2>/dev/null || true
        if "\$APP_EXEC" convert "\$FILE" >> "\$LOG_FILE" 2>&1; then
            BASE_NAME="\${FILE%.*}.pdf"
            notify-send -i "\$ICON" "SlidePDF Studio" "✓ Berhasil dikonversi:\n\$(basename "\$BASE_NAME")" 2>/dev/null || true
            ((COUNT++))
        else
            notify-send -u critical -i "\$ICON" "SlidePDF Studio" "✕ Gagal mengonversi \$(basename "\$FILE")" 2>/dev/null || true
        fi
    fi
done

if [ "\$COUNT" -gt 1 ]; then
    notify-send -i "\$ICON" "SlidePDF Studio" "Selesai! \$COUNT berkas berhasil dikonversi ke PDF." 2>/dev/null || true
fi
EOF
chmod +x "$NAUTILUS_SCRIPT"
echo "✓ Nautilus right-click script installed to $NAUTILUS_SCRIPT"

echo "========================================="
echo "  ✓ SlidePDF Studio Installation Complete! "
echo "========================================="
echo "You can now run: 'slidepdf' or 'pptx2pdf' from any terminal!"
