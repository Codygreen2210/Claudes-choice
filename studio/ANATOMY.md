# Anatomy for the 3D guy (study notes, 2026-10-24)

Why: the owner said the 3D guy doesn't look normal. Measuring him against real men showed why: his limbs were 20-26%
too thin, his waist and hips 13-14% too narrow, his chest too flat (front to back), and his face 18% too long.
These notes are the reference the sculpt (`samples/char/character.py`) is now built from, and `samples/char/measure.py`
checks him against these numbers on every build.

## 1. Build order (how a figure artist builds a body)

1. **Skeleton landmarks first.** Proportions come from bones: skull, ribcage, pelvis, shoulder girdle (clavicle +
   scapula), long bones. Where bone sits right under the skin it shows: collarbones, the sternal notch, the 7th
   neck vertebra, the acromion (shoulder point), elbow point (olecranon) and the two epicondyles, the wrist knobs,
   the iliac crest, the kneecap, the front of the shin (tibia), the ankle bones (malleoli).
2. **Muscles on the bones**, each from its origin to its insertion. A muscle is thickest in its belly and thins to
   tendon; a fan muscle (pecs, lats, glutes, deltoid, trapezius) is many fibres converging on one insertion.
3. **Fat and skin over everything.** A normal (not bodybuilder) man has a few mm of fat everywhere that rounds the
   muscle edges, more on the lower belly, flanks ("love handles"), buttocks and the back of the arm. This is why
   real bodies look smooth, with muscles read as broad planes, not separate lumps.

## 2. Body targets (adult man, scaled to our 175 cm)

| measure | real (cm) | source |
|---|---|---|
| stature | 175 (sample 177.7) | Heinz et al. 2003 |
| biacromial (bony shoulder) breadth | 41.2 | Heinz et al. 2003 (ANSUR II: 41.6) |
| chest girth (nipple) | 101.0 | Heinz et al. 2003 |
| chest breadth (bone) / depth (bone) | 29.9 / 20.8 | Heinz et al. 2003 |
| waist girth (narrowest) | 84.5 | Heinz et al. 2003 |
| navel girth | 87.7 | Heinz et al. 2003 |
| hip girth (buttocks) | 97.8 | Heinz et al. 2003 |
| bi-iliac / bitrochanteric breadth (bone) | 28.1 / 32.5 | Heinz et al. 2003 |
| neck girth | ~39.7 | ANSUR II |
| upper arm (biceps, flexed) | 34.4 (relaxed ~31.6) | Heinz et al. 2003 |
| forearm (max) | 28.2 | Heinz et al. 2003 |
| wrist | 17.2 | Heinz et al. 2003 |
| thigh (below gluteal fold) | 56.5 | Heinz et al. 2003 |
| knee | 37.2 | Heinz et al. 2003 |
| calf (max) | 37.2 | Heinz et al. 2003 |
| ankle (min) | 23.2 | Heinz et al. 2003 |

Cross-section shapes (width : depth): upper arm ~1 : 1.05, forearm near the elbow 1.2 : 1 flattening to 1.5 : 1 at
the wrist, thigh ~1 : 1, calf ~0.85 : 1 (deeper than wide, belly behind and toward the inside), trunk a rounded
rectangle (not an ellipse; a squarish chest is why a real chest girth is bigger than an ellipse of the same breadth
and depth).

## 3. Head and face targets

| measure | mm | source |
|---|---|---|
| head breadth / length / circumference | 154.3 / 199.5 / 574.4 | ANSUR II |
| bizygomatic (cheekbone) breadth | 143.5 | NIOSH 2005 (ANSUR II 142.6) |
| bigonial (jaw angle) breadth | 120.4 | NIOSH 2005 |
| menton-sellion (chin to nasal bridge) | 122.7 | NIOSH 2005 |
| subnasale-sellion (nose height) | 52.0 | NIOSH 2005 |
| nose breadth / protrusion | 36.6 / 21.1 | NIOSH 2005 |
| lip length (mouth width) | 51.1 | NIOSH 2005 |
| interpupillary | 64.5 | NIOSH 2005 |
| minimum frontal breadth (temples) | 105.5 | NIOSH 2005 |

Face landmarks: the **sellion** is the deepest point of the nasal bridge between the eyes, 6-8 mm behind the brow
ridge (glabella); the eyes sit at half the head height; ears span brow to nose base; mouth corners line up under the
pupils' inner edge; the jaw angle sits under the ear lobe, 2-3 cm narrower than the cheekbones on each side.

## 4. Skeleton landmark heights (fraction of stature, Drillis & Contini segment ratios)

vertex 1.000 · chin 0.870 · shoulder (acromion) 0.818 · nipple 0.720 · elbow 0.630 · navel ~0.600 · iliac crest
~0.590 · wrist 0.485 · greater trochanter / hip joint 0.530 · crotch 0.470 · fingertip 0.377 · knee 0.285 ·
ankle 0.039.  Segment lengths: upper arm 0.186 H, forearm 0.146 H, hand 0.108 H, thigh 0.245 H, shank 0.246 H.

## 5. Muscle layout (origin → insertion; what shows on the surface)

**Neck / shoulder girdle**
- Sternocleidomastoid: sternum + inner clavicle → mastoid behind the ear. The V from ear to collarbone notch.
- Trapezius: occiput + neck/thoracic spines → outer clavicle, acromion, scapular spine. The slope from neck to shoulder; a diamond on the upper back.
- Deltoid: outer clavicle, acromion, scapular spine → deltoid tuberosity (mid-humerus, outside). Three heads (front, side, back) cap the shoulder; it ends in a V halfway down the upper arm.

**Chest / trunk**
- Pectoralis major: inner clavicle, sternum, upper ribs → humerus just below the shoulder (lateral lip of the intertubercular groove). A broad, flat, squarish plate with a lower edge that runs up and out into the armpit fold. Not a mound.
- Serratus anterior: ribs 1-8 (side) → inner border of the scapula. Finger-like slips on the side of the ribcage below the armpit.
- Latissimus dorsi: lower thoracic/lumbar spine, iliac crest, lower ribs → humerus (front, near the pec). Makes the back wide (the V) and the back fold of the armpit.
- Rectus abdominis: pubis → lower sternum and ribs 5-7. A long flat strap, about 8 cm wide each side, with tendinous lines; on a normal man the belly is smooth with a soft linea alba.
- External oblique: lower ribs → iliac crest and the linea alba. Fills the flank; with a little fat on top it rounds the waist ("love handles").
- Erector spinae: sacrum/ilium → ribs and vertebrae. Two columns either side of the spine groove in the lower back.

**Arm**
- Biceps brachii: scapula (coracoid + supraglenoid) → radial tuberosity. Front of the upper arm; belly in the lower half.
- Brachialis: lower front humerus → ulna. Shows either side of the biceps above the elbow.
- Triceps brachii: scapula + back of humerus → olecranon. Back of the upper arm, a horseshoe with a flat tendon plate above the elbow.
- Brachioradialis: lateral supracondylar ridge of the humerus → radius at the wrist (thumb side). The bulge on the thumb side of the upper forearm.
- Wrist flexors (medial epicondyle → palm side) and extensors (lateral epicondyle → back of hand): the forearm is widest just below the elbow and tapers to a flat, narrow wrist.

**Hip and leg**
- Gluteus maximus: ilium, sacrum, coccyx → gluteal tuberosity / IT band. The buttock; the gluteal fold under it.
- Gluteus medius: outer ilium → greater trochanter. Fills the side of the hip below the iliac crest.
- Quadriceps: rectus femoris (pelvis, AIIS) and the vasti (femur) → patella → tibial tuberosity. Front of the thigh; vastus medialis makes the teardrop above the knee on the inside, vastus lateralis the long outer sweep.
- Sartorius: ASIS → upper inner tibia. The long diagonal strap that separates front and inner thigh.
- Adductors: pubis → inner femur. The inner upper thigh mass.
- Hamstrings: ischial tuberosity → tibia and fibula below the knee. Back of the thigh.
- Gastrocnemius: two heads on the femoral condyles → calcaneus via the Achilles tendon. The calf; the inner head is bigger and lower.
- Soleus: tibia and fibula → Achilles. Widens the lower calf at the sides.
- Tibialis anterior: lateral tibia → medial foot. The front shin muscle beside the bare tibia.

## 6. Male fat pattern (normal build)

Thin fat over the shoulders, arms (thicker on the back of the upper arm), chest and back; more on the lower
abdomen below the navel, the flanks above the iliac crest, the buttocks and the upper thighs. Fat softens the muscle
edges: a muscle's border shows as a soft change of plane, not a groove.

## 7. How it is built now (2026-10-24)

- Trunk, upper arm, forearm, thigh and shin are `loft` masses: rounded-rectangle (superellipse) sections at measured
  stations along the bone, interpolated smoothly (PCHIP) so there is no crease at any station. The trunk's front is
  squarer than its back (a man's chest is a broad flat plane; the back is rounder).
- Muscles sit on top as low relief (2-10 mm, small blend radius), placed origin-to-insertion: pec plates, deltoid
  heads, biceps/triceps, brachioradialis, vastus medialis teardrop, gastrocnemius heads, glutes, lats, trapezius,
  scapulae, infraspinatus to the back of the shoulder. Bone shows where it should: clavicles, sternal notch, C7,
  olecranon, epicondyles, patella, shin crest, malleoli, ulna head.
- Face: brow ridge forward of a real nasal-bridge dip (sellion), nose tip out to 21 mm, cheekbones in to 146 mm,
  skull trimmed to ANSUR size, upper lid lowered (less staring); lid edges are exported to the shader.
- Result (mm, before -> after -> real): chest 879 -> 1022 -> 995, waist 680 -> 835 -> 832, hips 831 -> 956 -> 963,
  neck 361 -> 396 -> 397, upper arm 249 -> 318 -> 312, forearm 205 -> 291 -> 278, wrist 141 -> 178 -> 169,
  thigh 413 -> 561 -> 556, knee 307 -> 379 -> 366, calf 287 -> 381 -> 366, ankle 175 -> 225 -> 229,
  chin-to-bridge 132 -> 126 -> 123, nose 17 -> 21 -> 21.

## Sources

- Heinz G, Peterson LJ, Johnson RW, Kerk CJ. *Exploring relationships in body dimensions.* Journal of Statistics
  Education 11(2), 2003 (the `bdims` dataset: 247 physically active men; we computed the male means).
- Gordon CC et al. *2012 Anthropometric Survey of U.S. Army Personnel (ANSUR II).* NATICK/TR-15/007, 2014;
  head/face means via Real World Appeal's ANSUR II summary.
- Zhuang Z, Bradtmiller B. *Head-and-face anthropometric survey of U.S. respirator users.* NIOSH/Anthrotech, 2005.
- Winter DA. *Biomechanics and Motor Control of Human Movement* (Drillis & Contini segment ratios).
- TeachMeAnatomy / Kenhub muscle attachment pages (pectoralis major, deltoid, latissimus dorsi, quadriceps, etc.).
