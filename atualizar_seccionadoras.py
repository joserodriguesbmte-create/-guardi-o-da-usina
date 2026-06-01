"""
Atualiza todas as seccionadoras com os dados da placa Siemens LAV 2013.
Execute: py -3.12 atualizar_seccionadoras.py
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guardiao.db")

c = sqlite3.connect(DB)

tags = [
    "PMCA6-01","PMCA6-02","PMCA6-03","PMCA6-04","PMCA6-05",
    "PMSD6-01","PMSD6-02","PMSD6-03","PMSD6-04","PMSD6-05","PMSD6-06","PMSD6-07",
    "PMSB6-01","PMSB6-02","PMSB6-03","PMSB6-04","PMSB6-05","PMSB6-06",
    "PMSB6-07","PMSB6-08","PMSB6-09","PMSB6-10",
    "PMSY6-01","PMSY6-02","PMSY6-03","PMSY6-04","PMSY6-05",
]

ok = 0
for tag in tags:
    c.execute("""UPDATE equipamentos SET
        fabricante      = 'Siemens',
        modelo          = 'LAV',
        ano_fabricacao  = '2013',
        tensao_nominal  = 245,
        corrente_nominal = 2000,
        numero_serie    = '0857/2013',
        observacao      = 'Norma: NBR IEC 62271-102/2007 | Contrato: 108753 | id: 104 kA | It/t: 40/1 kAs | M.Polo: 570 kg | M.Total: 1890 kg | Mecanismo MO-c: Torque 350 Nm / Tempo 13-15s / 104 kg | Cmd: 125Vcc / Motor: 440Vcc / Aquec: 220Vca 100W'
        WHERE tag = ?""", (tag,))
    if c.execute("SELECT changes()").fetchone()[0]:
        print(f"OK: {tag}")
        ok += 1
    else:
        print(f"NAO ENCONTRADO: {tag}")

c.commit()
c.close()
print(f"\n{ok} seccionadora(s) atualizada(s).")
