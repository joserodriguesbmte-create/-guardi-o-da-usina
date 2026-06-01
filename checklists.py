SISTEMAS = ["Subestação 230kV", "Sala Elétrica da SE", "Cúbilo de 13.8kV da SE",
            "Transformador TR-SE-01 (Toshiba 10/12.5 MVA)"]

CHECKLISTS = {
    "Subestação 230kV": [
        "Verificar condição geral dos equipamentos (disjuntores, seccionadoras, TCs, TPs)",
        "Verificar nível e cor do óleo dos transformadores",
        "Verificar pressão do SF6 nos disjuntores",
        "Verificar alarmes e sinalizações no painel de controle",
        "Verificar condição dos para-raios",
        "Verificar estado da sinalização e cartões de identificação",
        "Verificar sistema de aterramento",
        "Verificar condição da cerca e acesso à subestação",
        "Verificar limpeza e conservação da área externa",
        "Verificar iluminação interna e externa da SE",
        "Registrar leituras dos medidores (tensão, corrente, potência)",
        "Verificar sistema de proteção — relés em serviço",
    ],
    "Sala Elétrica da SE": [
        "Verificar temperatura ambiente da sala (máx. 35°C)",
        "Verificar funcionamento do ar-condicionado / ventilação",
        "Verificar condição dos painéis e cubículos elétricos",
        "Verificar sistema de iluminação de emergência",
        "Verificar extintores (prazo de validade e lacre)",
        "Verificar organização e limpeza da sala",
        "Verificar ausência de vazamentos ou infiltrações",
        "Verificar condição dos cabos e bandejas de cabos",
        "Verificar cartões de identificação dos painéis",
        "Verificar sistema de alarme de incêndio",
        "Verificar registros de temperatura nos painéis (termografia)",
        "Verificar estado do piso elevado (se aplicável)",
    ],
    "Cúbilo de 13.8kV da SE": [
        "Verificar posição das chaves e disjuntores (aberto/fechado)",
        "Verificar indicadores de tensão presentes",
        "Verificar ausência de alarmes ativos",
        "Verificar temperatura dos compartimentos (câmara de AR)",
        "Verificar condição das barras e conexões",
        "Verificar sistema de bloqueio e intertravamento",
        "Verificar sinalização de segurança e EPI disponível",
        "Verificar limpeza interna do cubículo",
        "Verificar estado dos isoladores e buchas",
        "Verificar registros de medição (A, V, kW)",
        "Verificar funcionamento das lâmpadas indicadoras",
        "Verificar condição da porta e vedação do cubículo",
    ],
    "Transformador TR-SE-01 (Toshiba 10/12.5 MVA)": [
        # Temperatura e Óleo — NBR 5356 + INTEC
        "Registrar leitura do OTI (Termômetro de Óleo) — máx. elevação 65°C",
        "Registrar leitura do WTI AT (Termômetro de Enrolamento AT) — máx. elevação 65°C",
        "Registrar leitura do WTI BT (Termômetro de Enrolamento BT) — máx. elevação 65°C",
        "Verificar nível de óleo no conservador (visíglass) — nível entre mín. e máx.",
        "Verificar cor e aspecto do óleo (transparente/amarelo claro = normal)",
        "Verificar ausência de vazamentos de óleo no tanque, buchas e conservador",
        # Proteções
        "Verificar relé Buchholz — contatos de alarme e trip sem atuação",
        "Verificar DGPT2 (Detector de Gás, Pressão e Temperatura) — sem alarme ativo",
        "Verificar válvula de alívio de pressão — sem atuação recente",
        "Verificar termostatos — alarme e desligamento sem atuação",
        "Verificar relé diferencial (87T) em serviço no painel",
        "Verificar relé de sobrecorrente (50/51) em serviço",
        # Resfriamento ONAN/ONAF
        "Verificar funcionamento dos ventiladores (ONAF) — acionar e confirmar rotação",
        "Verificar limpeza dos radiadores — sem entupimento ou sujidade excessiva",
        "Verificar temperatura de comutação automática ONAN → ONAF",
        # Comutador de Tap
        "Registrar posição atual do comutador (DETC) — tap em uso",
        "Verificar ausência de ruídos anormais no comutador",
        # Isolação e Partes Mecânicas
        "Verificar condição das buchas AT (230kV) — sem trincas, vazamentos ou sujidade",
        "Verificar condição das buchas BT — sem trincas, sujidade ou arborescências",
        "Verificar integridade das conexões de aterramento",
        "Verificar conservador/expansor de óleo — nível e estado da membrana",
        # Painel e Sinalizações
        "Verificar ausência de alarmes no painel local do transformador",
        "Verificar lâmpadas indicadoras do painel — todas operacionais",
        "Verificar identificação e cartões de segurança atualizados",
        # Área e Conservação
        "Verificar limpeza e drenagem da bacia de contenção de óleo",
        "Verificar ausência de animais, ninhos ou objetos estranhos",
        "Registrar temperatura ambiente no momento da inspeção",
    ],
}

ITENS_5S = {
    "Subestação 230kV": [
        "Área livre de materiais desnecessários",
        "Equipamentos organizados e identificados",
        "Piso limpo e sinalizado",
        "Ferramentas guardadas após uso",
        "Normas de segurança visíveis",
    ],
    "Sala Elétrica da SE": [
        "Sala organizada sem materiais estranhos",
        "Cabos e fiações organizados",
        "Piso limpo e desobstruído",
        "Documentação atualizada e organizada",
        "Normas e procedimentos afixados",
    ],
    "Cúbilo de 13.8kV da SE": [
        "Área do cubículo livre e sinalizada",
        "Ferramentas e EPIs organizados",
        "Painel limpo e sem poeira",
        "Etiquetas e cartões atualizados",
        "Extintor próximo e em bom estado",
    ],
    "Transformador TR-SE-01 (Toshiba 10/12.5 MVA)": [
        "Bacia de contenção limpa e sem óleo acumulado",
        "Área ao redor livre e sinalizada",
        "Painéis e instrumentos limpos e legíveis",
        "Identificações e cartões de segurança afixados",
        "EPIs disponíveis para acesso à área",
    ],
}
