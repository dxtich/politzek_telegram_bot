import json

user_stat = dict()
text_stat = dict()

with open("a.log", "r") as l:
    for line in l.readlines():
        try:
            if (line[19:25] == "|INFO|" or line[0:9] == 'INFO:bot:') and ("cache" not in line):
                if line[0].isdigit():
                    jline = line[25:]
                else:
                    jline = line[9:]
                jmessage = json.loads(jline)

                user = jmessage["from"]
                id = user["id"]
                user_stat.setdefault(id, {'count': 0, 'user': user})
                user_stat[id]['count'] += 1

                text = jmessage["text"]
                text_stat.setdefault(text, 0)
                text_stat[text] += 1

        except Exception as e:
            None

user_stat = {k: v for k, v in sorted(user_stat.items(), key=lambda item: item[1]['count'], reverse=True)}
text_stat = {k: v for k, v in sorted(text_stat.items(), key=lambda item: item[1], reverse=True)}

print("Users:")
for k, v in user_stat.items():
    print(f"{k}: {v}")

print("\n\n\nTexts:")
for t in text_stat:
    print(f"{t}: {text_stat[t]}")

