import json
# Midway POV sample: "you are" narration, rotating through three men, with the camera in their eyes.
def L(d,s,b=0,cap=None): return [d,s,b,cap]
sc=[
# 0: McClusky's cockpit
[L(-.2,"You are Wade McClusky, nearly twenty thousand feet over the Pacific.",0,"You are Wade McClusky, nearly 20,000 feet over the Pacific."),
 L(.1,"Your fuel needle is touching the point where you should turn back.",1),
 L(.2,"About thirty dive bombers are following you. Every one of them is watching your plane."),
 L(.1,"The enemy fleet was supposed to be right here."),
 L(-.3,"There is nothing below you but ocean.",1),
 L(.2,"Then you see it. One thin white line on the water."),
 L(.1,"A Japanese destroyer, alone, racing north.",1),
 L(-.4,"You follow it.")],
# 1: Nagumo's binoculars
[L(.0,"You are Admiral Nagumo, on the bridge of the carrier Akagi.",1),
 L(.2,"All morning, American planes have come at you low over the water."),
 L(.1,"Your fighters have knocked them down, one after another.",1),
 L(-.3,"Not one torpedo has hit."),
 L(.1,"Your fighters are all down low now, chasing the last of them."),
 L(-.5,"Nobody is watching the sky.",1)],
# 2: George Gay, low over the water
[L(.1,"You are George Gay. You are twenty five years old, and this is your first combat mission.",0,"You are George Gay. You are 25 years old, and this is your first combat mission."),
 L(.3,"To drop your torpedo, you have to fly low and straight, right into the guns.",1),
 L(.2,"Every plane in your squadron goes into the sea. Yours too.",1),
 L(-.2,"Of thirty men, you are the only one still alive."),
 L(-.4,"You float in the wreckage, and you look up.",1)],
# 3: the dive, through McClusky's sight
[L(.1,"You are McClusky again. It is ten twenty two.",0,"You are McClusky again. It is 10:22."),
 L(.3,"You roll over, and point your nose straight down at a flight deck with a big red circle on it.",1),
 L(.2,"It grows in your sight. Planes, fuel hoses, bombs, all out in the open."),
 L(.4,"Release.",1),
 L(.1,"You pull out low over the water, and you look back.",1),
 L(-.3,"In about five minutes, three of the carriers that bombed Pearl Harbor are on fire.",1),
 L(.1,"But one of them got away."),
 L(-.5,"And it was coming for the Yorktown.")],
]
REP={'Nagumo':'Nahgoomo','Akagi':'Ahkahgee','McClusky':'McClusky'}
for S in sc:
    for l in S:
        sp=l[1]
        for a,b in REP.items(): sp=sp.replace(a,b)
        if sp!=l[1]:
            if l[3] is None: l[3]=l[1]
            l[1]=sp
json.dump({"title":"Midway POV sample","voice":"studio voice: Kokoro am_michael 0.75 + am_eric 0.25, style B","note":"each line: [delivery -1 soft .. +1 sharp, what is said, 1 if a held beat follows, what the caption shows if different]","scenes":sc},open('script.json','w'),indent=1)
print(sum(len(l[1].split()) for s in sc for l in s),'words')
