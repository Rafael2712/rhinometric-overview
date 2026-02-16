#!/usr/bin/env python3
"""
Script para traducir documentos Markdown de ES a EN manteniendo formato exacto
"""

import re

def translate_doc(input_file, output_file, doc_type):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Traducciones comunes para todos
    common_translations = {
        '**Fecha:**': '**Date:**',
        '**Versión:**': '**Version:**',
        '**Estado:**': '**Status:**',
        '**Fuente:**': '**Source:**',
        '**Documento generado a partir de archivos verificables del repositorio.**': '**Document generated from verifiable repository files.**',
        '**Última actualización:**': '**Last update:**',
        '**Versión del documento:**': '**Document version:**',
        'Producción Operativa': 'Production Operational',
        'Basado en': 'Based on',
        'Según': 'According to',
        'archivos de configuración': 'configuration files',
        '(Verificado)': '(Verified)',
        '(Documentadas)': '(Documented)',
        '(Estimaciones)': '(Estimates)',
        '*Nota:': '*Note:',
        'Completado:': 'Completed:',
        'En Desarrollo:': 'In Development:',
        'Planeado/Pendiente:': 'Planned/Pending:',
        'Producción operativa con mejoras pendientes': 'Production operational with pending improvements',
        'Este documento lista ÚNICAMENTE las tareas pendientes documentadas en el repositorio, sin inventar funcionalidades.': 'This document lists ONLY pending tasks documented in the repository, without inventing features.',
        '**Archivo fuente:**': '**Source file:**',
        '**Status:**': '**Status:**',
        '**Tiempo estimado:**': '**Estimated time:**',
        'Pendiente': 'Pending',
        'No implementado': 'Not implemented',
        'Parcialmente implementado': 'Partially implemented',
        '**Problema documentado:**': '**Documented problem:**',
        '**Tareas:**': '**Tasks:**',
        '**Archivos a modificar:**': '**Files to modify:**',
        '**Entregables:**': '**Deliverables:**',
        '**Funcionalidad:**': '**Functionality:**',
        '**Funcionalidades:**': '**Features:**',
        '**Templates:**': '**Templates:**',
        '**Script:**': '**Script:**',
        '**Componentes:**': '**Components:**',
        '**Tech Stack:**': '**Tech Stack:**',
        '**Arquitectura:**': '**Architecture:**',
        '**Visión:**': '**Vision:**',
        'horas': 'hours',
        'minutos': 'minutes',
        'semanas': 'weeks',
        'Objetivo Q': 'Goal Q',
        'Objetivos Q': 'Goals Q',
        'Resultado esperado:': 'Expected result:',
        'Focus:': 'Focus:',
        'líneas': 'lines',
    }
    
    # Aplicar traducciones comunes
    result = content
    for es, en in common_translations.items():
        result = result.replace(es, en)
    
    # Traducciones específicas por tipo de documento
    if doc_type == 'backlog':
        backlog_translations = {
            '# RHINOMETRIC v2.5.0  \n## Backlog de Desarrollo y Pendientes': '# RHINOMETRIC v2.5.0  \n## Development Backlog and Pending Items',
            '## Resumen de Estado': '## Status Summary',
            '## 🔴 PRIORIDAD CRÍTICA (Próximas 2 semanas)': '## 🔴 CRITICAL PRIORITY (Next 2 weeks)',
            '## 🟡 PRIORIDAD ALTA (Próximas 4 semanas)': '## 🟡 HIGH PRIORITY (Next 4 weeks)',
            '## 🟢 PRIORIDAD MEDIA (Próximos 2-3 meses)': '## 🟢 MEDIUM PRIORITY (Next 2-3 months)',
            '## 🔵 PRIORIDAD BAJA (Backlog - 6+ meses)': '## 🔵 LOW PRIORITY (Backlog - 6+ months)',
            '## 📊 Resumen de Esfuerzo': '## 📊 Effort Summary',
            '## 🎯 Roadmap Propuesto': '## 🎯 Proposed Roadmap',
            '## 💰 Estimación de Inversión': '## 💰 Investment Estimate',
            '## ✅ Próximos Pasos Inmediatos': '## ✅ Immediate Next Steps',
            '## Issues Técnicos Conocidos': '## Known Technical Issues',
            '## Notas de Implementación': '## Implementation Notes',
            '**Referencias:**': '**References:**',
            '### Desglose por Prioridad': '### Breakdown by Priority',
            '### Recursos Necesarios': '### Required Resources',
            '**Desarrollo:**': '**Development:**',
            '**Infraestructura:**': '**Infrastructure:**',
            '**Otros:**': '**Other:**',
            '**Total Dev:**': '**Total Dev:**',
            '**Total Infra:**': '**Total Infra:**',
            '**Total Otros:**': '**Total Other:**',
            '**TOTAL AÑO 1:**': '**TOTAL YEAR 1:**',
            'Equivalente en Semanas (1 dev)': 'Equivalent in Weeks (1 dev)',
            'Horas Totales': 'Total Hours',
            '**Prioridad**': '**Priority**',
            '**Tareas**': '**Tasks**',
            '**TOTAL**': '**TOTAL**',
            'Crítica': 'Critical',
            'Alta': 'High',
            'Media': 'Medium',
            'Baja': 'Low',
            'Corregir Enlaces del Email Annual': 'Fix Annual Email Links',
            'Implementar Backup Automático de Base de Datos': 'Implement Automatic Database Backup',
            'Migrar Stack Legacy y Eliminar Containers Crasheando': 'Migrate Legacy Stack and Remove Crashing Containers',
            'Implementar Monitoreo Completo': 'Implement Complete Monitoring',
            'Notificaciones Automáticas de Expiración de Licencias': 'Automatic License Expiration Notifications',
            'Portal de Cliente Self-Service': 'Self-Service Client Portal',
            'Sistema de Facturación Integrado': 'Integrated Billing System',
            'API Pública Documentada': 'Documented Public API',
            'Alertas Inteligentes y Webhooks': 'Smart Alerts and Webhooks',
            'Multi-Región (EU Datacenter)': 'Multi-Region (EU Datacenter)',
            'Mobile App (iOS + Android)': 'Mobile App (iOS + Android)',
            'Mejoras del Motor de Detección de Anomalías Existente': 'Improvements to Existing Anomaly Detection Engine',
            'Kubernetes Monitoring Nativo': 'Native Kubernetes Monitoring',
            'Custom Plugins Marketplace': 'Custom Plugins Marketplace',
            'White-Label Solution': 'White-Label Solution',
            'Enterprise SSO (SAML, OAuth)': 'Enterprise SSO (SAML, OAuth)',
            'Cloud Cost Optimization': 'Cloud Cost Optimization',
            'Compliance Automation (SOC 2, ISO 27001)': 'Compliance Automation (SOC 2, ISO 27001)',
            'On-Premise Installer (Air-Gapped)': 'On-Premise Installer (Air-Gapped)',
            'Multi-Tenancy Completo': 'Complete Multi-Tenancy',
            'Motor básico implementado en v2.5.0': 'Basic engine implemented in v2.5.0',
            'mejoras planeadas para': 'improvements planned for',
            '**Severidad:**': '**Severity:**',
            '**Containers afectados:**': '**Affected containers:**',
            '**Problema:**': '**Problem:**',
            '**Solución propuesta:**': '**Proposed solution:**',
            '**Cobertura:**': '**Coverage:**',
            '**Faltante:**': '**Missing:**',
            'Estabilización y mejoras operacionales': 'Stabilization and operational improvements',
            'Expansión de funcionalidades': 'Feature expansion',
            'Escalabilidad y nuevos canales': 'Scalability and new channels',
            'Enterprise y compliance': 'Enterprise and compliance',
            'Plataforma production-ready al 100%': 'Platform 100% production-ready',
            'Funcionalidad enterprise': 'Enterprise functionality',
            'Plataforma multi-plataforma': 'Multi-platform platform',
            'Enterprise-grade platform': 'Enterprise-grade platform',
            'Esta Semana:': 'This Week:',
            'Próxima Semana:': 'Next Week:',
            'Este Mes:': 'This Month:',
            '**Tests Automatizados**': '**Automated Tests**',
            '**Documentación**': '**Documentation**',
            'Pendiente:': 'Pending:',
            'falta': 'missing',
        }
        for es, en in backlog_translations.items():
            result = result.replace(es, en)
    
    elif doc_type == 'technical':
        # El técnico ya fue traducido por el otro script
        pass
    
    # Guardar resultado
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f'✅ Traducido: {input_file} → {output_file}')

# Traducir backlog
translate_doc(
    'BACKLOG_RHINOMETRIC_FACTUAL.md',
    'DEVELOPMENT_BACKLOG_RHINOMETRIC_FACTUAL.md',
    'backlog'
)

print('\n✅ Traducción completada!')
