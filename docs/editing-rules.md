# Editing rules for History_Unfoldz films

How the films are cut: shot by shot, sound against picture, and how the whole thing breathes.
Each rule says where it comes from so it can be argued with. `studio/senses/editcheck.py` measures
the ones a machine can measure; the rest are checked by eye on the contact sheet before rendering.

## The order of what matters (Walter Murch, *In the Blink of an Eye*)
Murch, who cut *Apocalypse Now* and *The English Patient*, ranks what a cut must serve:
**emotion 51%, story 23%, rhythm 10%, eye trace 7%, 2D plane 5%, 3D space 4%.**
When two rules fight, the higher one wins. A cut that feels right but breaks screen direction stays;
a cut that is "correct" but kills the feeling goes.

## Picture

1. **Cut on the feeling, not the line.** Hold a shot until the audience has felt what it's for, then
   one beat less. Every shot gets a job written next to it in the script (`job:`): show, tell, feel, breathe.
2. **Shot length follows the story's pulse.** Documentary animation averages roughly 3 to 8 seconds a
   shot. Calm setup runs longer, the attack runs shorter. *Dunkirk* tightens the cutting as the three
   timelines converge, so the climax should cut at least 30% faster than the opening.
3. **Vary the rhythm.** Equal shot lengths read as a slideshow. Mix long and short like speech:
   long, long, short, short, short, long.
4. **Nothing sits dead.** Any shot over 15 s must move (push, pan, parallax, a character acting).
   Ken Burns' *The Civil War* never lets a still sit; the camera always drifts toward the detail
   the narrator is about to name.
5. **No flash frames.** Under 0.5 s only on purpose (a muzzle flash, an impact). Never by accident.
6. **Hide the hand-offs in POV (from *1917*).** *1917* hides its cuts in a dark doorway, a passing
   body, a whip pan. Our POV films change person by pushing through a shared object (the destroyer,
   a cloud, smoke, glare). Never hard-cut from one person's eyes into another's.
7. **Keep screen direction.** Americans fly left to right, Japanese right to left, for the whole film.
   Who is chasing whom must read without words. Break it only to show a turn in the story.
8. **Withhold the monster (from *Jaws*).** For man-eater and threat stories, show traces first
   (tracks, a moving branch, a sound off-screen) and the full animal late. The reveal earns its place.
9. **Pillow shots.** After a big moment, cut to something still and wordless (water, smoke, sky,
   an empty deck) for 4 to 8 seconds before the narration comes back. This gives the audience
   room to feel what just happened. Every film has at least one, right after the climax.
10. **Explain the money with pictures (from *The Big Short*).** Finance stories cut away to one
    plain visual per idea (a stack of coupons, a line of people, a number filling the screen)
    instead of narration over a chart. One idea per shot.
11. **Patience, then payoff (from BBC *Planet Earth*).** Animal stories hold on the wait (the stalk,
    the grass moving) longer than feels comfortable, then cut fast on the strike.
12. **Open cold, end slow.** Picture and sound start at 0.0 s mid-action, no logo or fade-in.
    The last shot holds at least 3 s and resolves.

## Sound against picture

13. **J and L cuts.** Most cuts should not change sound and picture at the same instant.
    A J-cut lets the next scene's sound arrive 0.5 to 2 s early (the engines before we see the
    planes). An L-cut lets this scene's sound carry over the cut. Hard sound-and-picture cuts are kept
    for shocks. Target: at least 30% of cuts are J or L.
14. **Silence before the hit (from *Saving Private Ryan* and *Dunkirk*).** Drop the music, and often
    most of the sound, for 1 to 3 s right before the biggest moment. The drop makes the hit land.
15. **Subjective sound in POV.** When we're inside someone's head, the sound is theirs: the muffled
    ringing after a blast (*Saving Private Ryan*), the engine filling the cockpit, the heartbeat while
    waiting. Leave POV, and the sound opens back up.
16. **The ticking clock (from *Dunkirk*).** A low steady pulse under rising tension (a watch, engine
    rpm, a drum), getting faster or louder as time runs out. Stop it dead at the climax.
17. **Music enters late and leaves early.** Start a cue on a cut or a look, not on a line of narration.
    Pull it out before the scene ends so the next scene starts clean.

## Story shape

18. **Hook, question, turn, climax, breath, meaning.** Open on the promise (cold open), pose the
    question the film will answer, turn it at least once (what the audience thought was true isn't),
    climax, pillow shot, then what it meant then and what it means now.
19. **One point of view per stretch.** Stay with a person long enough to care (at least about 20 s)
    before handing off. Rapid switching is saved for the climax.
20. **Show what the narration doesn't say.** If the narrator says it, the picture adds something else.
    Never picture a word the narrator just said; picture its consequence.

## How to use
- Write `job:` on every shot in `mkscript.py`; plan pillow shots and J/L cuts in the script, not in the mix.
- Before rendering: contact sheet by eye (rules 1, 6 to 11, 15, 18 to 20).
- After rendering: `python3 studio/senses/editcheck.py film.mp4 --climax <seconds>`. It must score 80+
  before the film goes to Cody, along with listen.py, pacing.py and thumbcheck.

Sources: Walter Murch, *In the Blink of an Eye* (Rule of Six); nofilmschool.com on the Rule of Six;
filmdaft.com on L- and J-cuts; the films named in each rule.
