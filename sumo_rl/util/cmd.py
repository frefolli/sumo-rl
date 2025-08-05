import os
PUNCHLINE_GOOD = "Il treno regionale veloce 24 77, di Trenitalia Tper, proveniente da Milano Centrale e diretto a Rimini, via Ravenna, delle ore 18 e 22, è in arrivo al binario 11."
PUNCHLINE_BAD = "Il treno regionale veloce 24 77, di Trenitalia Tper, proveniente da Milano Centrale e diretto a Rimini, via Ravenna, previsto in partenza alle ore 18 e 22, oggi non sarà effettuato. Per un guasto, al treno."
PUNCHLINE_S9 = "Il treno suburbano S9, 24 9 62 di Trenord, proveniente da Albairate-Vermezzo e diretto a Saronno, delle ore 12:56, è in arrivo al binario 2, invece che al binario 4. Attenzione! allontanarsi dalla linea gialla! Ferma in tutte le stazione eccetto: Cesano Maderno parco delle groane, Ceriano Laghetto parco delle groane."

def spd_say(msg: str):
  if os.path.exists('/usr/bin/spd-say'):
    os.system('spd-say -w -l it "%s"' % msg)
  else:
    print(msg)

def on_event_succed():
  spd_say(PUNCHLINE_GOOD)

def on_event_fail():
  spd_say(PUNCHLINE_BAD)

def on_event_S9():
  spd_say(PUNCHLINE_S9)

def exec_cmd(cmd: str) -> None:
  print('CMD:', cmd)
  if os.system(cmd) != 0:
    on_event_fail()
    raise ValueError(cmd)
