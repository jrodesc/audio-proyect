#!/usr/bin/env python3
"""
YouTube Audio Player - Reproductor de audio de YouTube sin anuncios
"""
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """Punto de entrada de la aplicación"""
    app = QApplication(sys.argv)
    
    # Configurar nombre de la aplicación
    app.setApplicationName("YouTube Audio Player")
    app.setOrganizationName("YT Audio")
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar aplicación
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
