import json
# Sources: Jim Corbett, Man-Eaters of Kumaon (1944), "The Champawat Man-Eater"; Guinness Book of Records (1997);
# Wikipedia, Champawat Tiger; Ripley's, The Tiger Queen; India tiger census 2022.
def L(d,s,b=0,cap=None): return [d,s,b,cap]
sc=[
# 0 the beat
[L(-.1,"The twelfth of May, nineteen oh seven. Noon. A river gorge in the hills of northern India.",1,"May 12, 1907. Noon. A river gorge in the hills of northern India."),
 L(.2,"Up on the ridge, almost three hundred men are spread out in a long line, beating drums, banging pots, and shouting as loud as they can.",0,"Up on the ridge, almost 300 men are spread out in a long line, beating drums, banging pots, and shouting as loud as they can."),
 L(.1,"Down on the floor of the gorge, one man waits alone, with a rifle.",1),
 L(.0,"The noise is meant to drive something toward him.",0),
 L(-.2,"Something that has been hunting the people of these hills for years.",1),
 L(-.4,"By the time this day is over, it will be in the record books as the deadliest animal of its kind ever known.",0)],
# 1 Kumaon
[L(.2,"These are the hills of Kumaon, at the foot of the Himalayas.",0),
 L(.1,"Steep slopes, small villages, terraced fields cut into the mountainside, and thick forest everywhere in between.",1),
 L(.0,"Tigers and leopards had always lived in these hills, and people had always lived beside them.",1),
 L(.0,"Life here depended on that forest. Every day, women and children went into it for firewood, for grass to feed the cattle, for leaves and wood to make things.",1),
 L(.1,"But by nineteen oh seven, nobody in these villages went into the forest anymore.",0,"But by 1907, nobody in these villages went into the forest anymore."),
 L(.2,"The fields went untended. People stayed behind closed doors all day.",1),
 L(-.3,"And at night, the villages beat drums, so whatever was out there would know they were awake.",1)],
# 2 Nepal
[L(.1,"It had started across the border, in Nepal.",0),
 L(.2,"A tigress began taking people from the villages there, near a place called Rupal.",1),
 L(.1,"Hunters went after her, and failed. The killing went on.",0),
 L(.2,"Finally the government of Nepal sent the army.",1),
 L(.3,"Hundreds of soldiers formed a huge line and swept the forest, and drove her west... across the Sarda River, and into India.",0),
 L(-.2,"Most accounts say she had already killed about two hundred people in Nepal.",1,"Most accounts say she had already killed about 200 people in Nepal."),
 L(-.4,"The army had not stopped her. They had only moved her.",1)],
# 3 how she hunted
[L(.1,"In Kumaon, she did not stay in one place.",0),
 L(.2,"She could cover twenty miles in a night. A village would lose someone, and the next attack would be on the far side of the valley.",1,"She could cover 20 miles in a night. A village would lose someone, and the next attack would be on the far side of the valley."),
 L(.1,"Most tigers that hunt people do it in the dark. She hunted in broad daylight.",0),
 L(.0,"And most of the people she took were women and girls, out cutting grass or gathering wood, close to home.",1),
 L(-.2,"Every death was counted. And the count kept going up.",0),
 L(.1,"The government put a reward on her head. Hunters came from all over. None of them got her.",1),
 L(-.3,"Two hundred. Three hundred. Four hundred.",1,"200. 300. 400.")],
# 4 why
[L(.1,"Tigers do not normally hunt people.",1),
 L(.2,"A healthy tiger kills deer, wild pig, and buffalo. Big, fast animals that it brings down with its jaws.",0),
 L(.0,"The answer to why this one was different was not found until after she was dead.",1),
 L(.1,"Two of her big teeth, on the right side of her mouth, were broken. One in half. The other right down to the bone.",0),
 L(-.2,"Most likely, a hunter had shot her years before, and the bullet had smashed them.",1),
 L(-.3,"She could no longer hold and kill the animals she was built to hunt.",0),
 L(-.5,"People were slower. And easier.",1)],
# 5 Corbett
[L(.1,"The man in the gorge was named Jim Corbett.",0),
 L(.2,"He was thirty one years old. He had been born in these hills, in the town of Nainital, and had spent his childhood in the forest.",0,"He was 31 years old. He had been born in these hills, in the town of Nainital, and had spent his childhood in the forest."),
 L(.1,"He could read tracks. He knew the alarm calls of the birds and the deer, the sounds that say a tiger is moving.",1),
 L(.0,"He had a job working for the railway. Hunting was something he did on the side.",0),
 L(.2,"When the government asked him to help, he agreed, on two conditions.",1),
 L(.1,"The reward on her head had to be cancelled. And every other hunter had to be called off.",0),
 L(-.3,"He did not want to be paid for it. And he did not want anyone shooting at the wrong tiger... or at him.",1)],
# 6 the search
[L(.1,"He walked from village to village, following the news of each attack.",0),
 L(.0,"He was always too late. By the time he arrived, she had moved on.",1),
 L(.1,"Weeks went by. In each village, people showed him the path, the spring, the field, where someone had been taken.",1),
 L(.2,"Then he reached the town of Champawat, and met the local official, the tahsildar, who would stay at his side.",0),
 L(-.1,"And word came from a village nearby, called Phungar.",1)],
# 7 Phungar
[L(.1,"A sixteen year old girl named Premka Devi had gone out to collect firewood. She did not come back.",1,"A 16 year old girl named Premka Devi had gone out to collect firewood. She did not come back."),
 L(.2,"Corbett picked up the trail, and followed it into the forest.",0),
 L(.0,"It went down into a ravine, thick with brush.",1),
 L(-.2,"He found what was left of her. And as he knelt there, he had the feeling he was being watched.",1),
 L(-.3,"A little earth trickled down the bank above his head.",1),
 L(.4,"She was right there. Above him. Close enough to touch.",0),
 L(.2,"He swung his rifle up and fired twice. She disappeared into the brush.",1),
 L(-.3,"It was getting dark. Corbett knew better than to follow a tiger into thick cover at night. He went back to the village.",0)],
# 8 the plan
[L(.1,"The next morning, he made a plan.",1),
 L(.2,"She would not have gone far. She was resting somewhere in the gorge of a small river, the Champa.",0),
 L(.1,"The tahsildar went to every village around, and gathered every man who would come.",0),
 L(.0,"Two hundred and ninety eight of them.",1,"298 of them."),
 L(.2,"They would spread out along the top of the ridge, and walk down it, making all the noise they could.",0),
 L(-.2,"A tiger driven by noise moves away from it. Corbett would be waiting at the bottom.",1)],
# 9 the shot
[L(.1,"At noon, the drums started.",1),
 L(.2,"For a long time, nothing moved. Then she came out of the brush, onto the open floor of the gorge.",0),
 L(.3,"Corbett fired. The bullet hit. She turned, and kept coming.",1),
 L(.4,"He fired again, and hit her again.",1),
 L(-.2,"Then his rifle was empty.",1),
 L(.3,"The tahsildar had a gun. Corbett took it, and went after her.",0),
 L(-.3,"She was twenty feet away when he fired the last shot.",1,"She was 20 feet away when he fired the last shot."),
 L(-.5,"It was over.",1)],
# 10 the count
[L(.1,"The men came down off the ridge. Some of them would not go near her, even then.",1),
 L(.0,"Corbett looked at her mouth, and found the broken teeth.",0),
 L(.2,"Nobody knows exactly how many people she killed. The estimate most often given is four hundred and thirty six.",1,"Nobody knows exactly how many people she killed. The estimate most often given is 436."),
 L(-.2,"It is still listed as the most killed by any single tiger on record.",1),
 L(.0,"Today a small marker by the road, near the town of Lohaghat, shows the place where she fell.",0)],
# 11 after
[L(.1,"Corbett went back to his job at the railway.",1),
 L(.2,"But over the next thirty years, he was called back again and again, to hunt man-eating tigers and leopards all over Kumaon.",0),
 L(.1,"And slowly, he changed.",1),
 L(.2,"He traded his rifle for a camera. He wrote books about the forest. He warned that the tigers themselves were disappearing.",0),
 L(.1,"In nineteen forty four, he wrote it all down in a book, Man-Eaters of Kumaon. It sold all over the world.",1,"In 1944, he wrote it all down in a book, Man-Eaters of Kumaon. It sold all over the world."),
 L(.1,"In nineteen forty seven, he left India for Kenya. He died there, in nineteen fifty five.",1,"In 1947, he left India for Kenya. He died there, in 1955."),
 L(.0,"After he died, India named its first national park after him. Corbett National Park.",1),
 L(-.2,"It is one of the places where tigers are protected today.",0)],
# 12 today
[L(.1,"There are more wild tigers in India now than there have been in decades. Over three thousand.",0,"There are more wild tigers in India now than there have been in decades. Over 3,000."),
 L(.0,"And it is still true that a tiger that hunts people is almost always one that has been hurt, or is too old to hunt anything else.",1),
 L(-.2,"Corbett wrote that nine man-eaters out of ten had been wounded, and the tenth was too old to hunt.",0),
 L(-.3,"This one did not choose it.",1),
 L(-.4,"Somebody's bullet, years before, made that choice for her.",1),
 L(.4,"Subscribe, and we'll tell you more."),
 L(.2,"Everything from animal facts, to history's greatest battles, to the world's craziest financial collapses.")],
]
REP={"Kumaon":"Koo-maon","Nainital":"Nye-nee-tal","Premka Devi":"Prem-ka Day-vee","Phungar":"Foong-gar"}
for S in sc:
    for l in S:
        sp=l[1]
        for a,b in REP.items(): sp=sp.replace(a,b)
        if sp!=l[1]:
            if l[3] is None: l[3]=l[1]
            l[1]=sp
json.dump({"title":"The Champawat Tiger","voice":"studio voice: Kokoro am_michael 0.75 + am_eric 0.25, style B","note":"each line: [delivery -1 soft .. +1 sharp, what is said, 1 if a held beat follows, what the caption shows if different]","scenes":sc},open('script.json','w'),indent=1)
print(sum(len(l[1].split()) for s in sc for l in s),'words')
