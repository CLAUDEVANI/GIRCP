from pathlib import Path

p = Path("app_relatorio.py")
s = p.read_text(encoding="utf-8")

def sub(old, new):
    global s
    assert s.count(old) == 1, "trecho nao encontrado (ou repetido): " + old[:70]
    s = s.replace(old, new)

# 1) mapa: status que descrevem o que o dado realmente mostra; "Pendente" nunca era atribuido e sai
sub('status = "Concluída"', 'status = "Com evidências"')
sub('status = "Em Andamento"', 'status = "Sem evidências"')
sub('.map({"Concluída": "✅", "Em Andamento": "⚙️", "Pendente": "🕐"})', '.map({"Com evidências": "✅", "Sem evidências": "📷"})')
sub('''        if status_filtro == "✅ Concluída": df_mapa = df_mapa[df_mapa['status_visita'] == "Concluída"]
        elif status_filtro == "⚙️ Em Andamento": df_mapa = df_mapa[df_mapa['status_visita'] == "Em Andamento"]
        elif status_filtro == "🕐 Pendente": df_mapa = df_mapa[df_mapa['status_visita'] == "Pendente"]''',
'''        if status_filtro == "✅ Com evidências": df_mapa = df_mapa[df_mapa['status_visita'] == "Com evidências"]
        elif status_filtro == "📷 Sem evidências": df_mapa = df_mapa[df_mapa['status_visita'] == "Sem evidências"]''')
sub('status_opcoes = ["Todos", "✅ Concluída", "⚙️ Em Andamento", "🕐 Pendente"]', 'status_opcoes = ["Todos", "✅ Com evidências", "📷 Sem evidências"]')
sub('''<b>Concluída</b> — relatório com fotos<br>''', '''<b>Com evidências</b> — relatório com fotos<br>''')
sub('''<b>Em Andamento</b> — sem fotos ainda<br>
            <span style='color:#64748B;font-size:15px;'>●</span> <b>Pendente</b> — sem visita registrada<br>''',
    '''<b>Sem evidências</b> — laudo sem fotos<br>''')
sub('{n_concluidas}</div><div class="eng-metric-label">CONCLUÍDAS</div>', '{n_concluidas}</div><div class="eng-metric-label">COM EVIDÊNCIAS</div>')
sub('{n_andamento}</div><div class="eng-metric-label">EM ANDAMENTO</div>', '{n_andamento}</div><div class="eng-metric-label">SEM EVIDÊNCIAS</div>')
sub('<div class="eng-metric-label">C/ ANOMALIA CRÍTICA</div>', '<div class="eng-metric-label">LAUDOS C/ ANOMALIA CRÍTICA</div>')

# 2) orcamento: o cartao conta linhas de material, nao evidencias
sub('style="color:#DA291C;">{n_criticos}</div><div class="eng-metric-label">ITENS CRÍTICOS</div>',
    'style="color:#DA291C;">{n_criticos}</div><div class="eng-metric-label">MATERIAIS EM ITENS CRÍTICOS</div>')

# 3) rota: o rotulo informa o metodo (ORS ou linha reta a 40 km/h)
sub('            secao("KPI", "MÉTRICAS DA OPERAÇÃO DE CAMPO")',
    '''            _met_km = "VIA ORS" if geojson_rota else "LINHA RETA"
            _met_tempo = "ORS" if geojson_rota else "EST. 40 KM/H"
            secao("KPI", "MÉTRICAS DA OPERAÇÃO DE CAMPO")''')
sub('<div class="eng-metric-label">QUILOMETRAGEM ESTIMADA</div>', '<div class="eng-metric-label">QUILOMETRAGEM ({_met_km})</div>')
sub('<div class="eng-metric-label">WINDSHIELD TIME (DIREÇÃO)</div>', '<div class="eng-metric-label">TEMPO DE DIREÇÃO ({_met_tempo})</div>')

p.write_text(s, encoding="utf-8")
print("OK: Fase 3 aplicada em", p)
