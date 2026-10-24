# Rigging, posing and sculpting for animation: basics to advanced

Why this exists: limbs kept flying through the body and flailing 360 degrees in the socket. Every rule below is
now enforced in code (`studio/toon/rigsafe.py` for the house 2D guy, `studio/samples/l1/rig.py` for the hand-drawn
rig, `studio/samples/web/main.js` for the 3D rig) and checked by `rigcheck.py` / `rigcheck3d.*`.

## 1. The skeleton (basics)

- **A rig is a tree.** Root (hips) -> spine -> neck -> head; shoulders -> upper arm -> forearm -> hand;
  hips -> thigh -> shin -> foot. Each bone rotates about its **pivot at the joint** and carries its children with it.
  In cutout/2D rigs, every piece is placed under the part it moves with so its motion is relative to the parent
  (Godot cutout docs). Pivot in the wrong place = limbs that slide or detach.
- **Pose in local (parent-relative) angles, never world angles.** A world angle for the forearm ignores where the
  upper arm went, so nothing stops the elbow bending backwards or sideways. Local angles are what joint limits apply
  to, and blending them can't take the long way round. *This was our main bug.*
- **Rest pose / preferred angle.** Every rig has a neutral pose it returns to; IK uses a preferred angle to decide
  which way a joint bends (Maya: "Set Preferred Angle" is the fix for flipping IK chains).
- **Rotation order and joint orient.** Euler rotations are applied in an order; pick it per joint so the axis that
  moves most is evaluated last, and orient joints so one axis points down the bone and one is the bend axis
  (Maya rigging wiki: X down the chain, Z forward). A hinge (elbow/knee) should only ever rotate about one axis.

## 2. How far joints really move (normal range of motion, degrees)

| Joint | Range | Rig limit we use |
|---|---|---|
| Shoulder | flexion 180, extension 50, abduction 180, adduction ~50, int./ext. rotation 90/90 | elevation 0-180; back ~50; across the chest ~45-100 |
| Elbow | flexion 140, hyperextension 0 | hinge 0-145, one way only |
| Forearm | pronation 80, supination 80 | twist via the shoulder/forearm, +-70-90 |
| Wrist | flexion 60, extension 60, radial 20, ulnar 30 | |
| Hip | flexion 100-120, extension 30, abduction 40-45, adduction 20, int./ext. rot. 40/50 | fwd 120, side 45, back 30, across 30 |
| Knee | flexion 150, no hyperextension | hinge 0-150, folds backward only |
| Ankle | plantar 20(-50), dorsi 30 | |
| Neck | flexion 60, extension 75, lateral 45, rotation 80 | pitch -60..75, yaw +-80, roll +-45 |
| Lower back | flexion 45-50, extension 25, lateral 25, rotation 30 | |

Source: WikEM ROM table (Luttgens & Hamilton). Shoulder elevation past ~90-120 needs the shoulder blade:
after the first ~30 deg it moves about 2:1 (arm:scapula), 60 of the 180 comes from the scapula
(scapulohumeral rhythm), so a rig's arm must not stop at 90 but should show the shoulder lifting near the top.

**Ball joints are cones, not boxes.** The reachable directions of a shoulder or hip form an irregular cone: it lifts
180 forward/sideways but only ~50 backward. Game engines limit them as **swing** (two angles, a cone) plus
**twist** (rotation about the bone, low/high limit) (Unity Character Joint). Our 3D rig uses ISB-style
plane-of-elevation + elevation + twist, with the max elevation looked up per plane.

## 3. Limits that feel natural

- **Soft limits.** A hard clamp makes a moving limb stop dead and jitter. We ease into the limit
  (`soft_clamp`: identity inside, tanh-shaped approach in the last ~10 deg), the same idea as a joint limit spring
  with a damper (Unity: spring 0 = rigid, damper settles oscillation).
- **Clamp parent before child**, then rebuild the child from the clamped parent (FABRIK applies constraints at every
  joint during each pass, not only at the end).
- **Hinges are one-way.** Elbows fold forward, knees fold backward, never sideways. In a 2D front view, a knee can't
  visibly bend sideways more than ~10 deg (we allow +-12); an elbow can show either way (its twist is hidden).

## 4. IK without flipping

- **Two-bone IK** (arm/leg) has two answers (elbow up or down). Pick with a **pole vector / preferred angle** and keep
  that choice for the whole move (Maya rotate-plane solver + pole vector exists to stop flipping; single-chain
  solvers on 2 bones are not recommended).
- **Joint-limit-aware IK.** Our `rigsafe.ik_arm` searches only legal poses (inside limits, upper arm clear of the
  head, hand not past the far shoulder) and prefers the pose nearest the preferred one: it can never answer with an
  elbow through the head. The old exact solver could return a shoulder at -108 deg.
- **FABRIK** (Aristidou & Lasenby): forward/backward reaching passes along the chain, keeping bone lengths; joint
  limits are applied at every step by projecting onto an elliptical cone (ball joints) or onto the hinge plane.
  Good for long chains (tails, tentacles, spines). If a chain is perfectly straight and the target is on its line,
  bend it slightly first or it stalls.
- **Moving targets: blend angles, not positions.** Interpolating hand positions and re-solving each frame lets the
  elbow pop between solutions. `reach_move` solves once and blends the joint angles.

## 5. No 360-degree spins

- **Angles wrap.** -180 and +180 are the same direction; a naive blend from 170 to -170 swings 340 the long way.
  Always blend the wrapped difference (`lerp_angle`, `wrap180`).
- **Unroll tracks.** For sampled animation, take each step the short way from the previous *unrolled* value
  (Holden, "Unrolling Rotations"; the Euler filter in Maya/Max does the same: it keeps the rotation, changes only
  which equivalent angles represent it so the curve is continuous).
- **Quaternions: shortest path.** q and -q are the same rotation; if dot(q0, q1) < 0 negate one before slerp, or
  it takes the long way (Wikipedia, Slerp).
- **Never warp a flail's clock.** Slowing a character by remapping time inside sin() (T*(1-k)) makes the phase race;
  fade the amplitude instead (that was the black hole Short's spinning arms).
- **Speed cap.** Real fast limb motion is ~1000 deg/s; beyond ~25 deg per frame at 30 fps a joint reads as a pop.
  A pose change needs at least ~6-9 frames unless there's a cut.
- **Bounded flailing.** Panic is two incommensurate sines, amplitude <= 35 deg, <= 2.5 Hz, added to a base pose
  in local space (`flail`): it never winds up into a rotation.
- **The tumble belongs to the root.** A falling, spinning body rotates the hips/root only; the joints keep their
  local angles. Adding the spin to every joint is what made limbs spin in their sockets.

## 6. Nothing through the body (self-collision)

- **Model the body as capsules and spheres** (torso capsule, head sphere, limb capsules) and test distances:
  sphere-sphere, capsule-sphere (project the centre on the axis), capsule-capsule (closest points of the two
  segments), each against the sum of radii (NAO robot self-collision docs).
- **Resolve by changing the pose, not by hiding it:** swing the arm outward / reduce elbow flex, spread the legs,
  and re-check, a few iterations max (NAO solves it as "follow the command as closely as possible without closing
  the gap"). Our 3D rig: hand 3 cm inside the chest -> pushed clear; crossed legs 17 cm overlap -> spread.
- **2D draw order is part of collision.** In a front view the arm is drawn before the head, so a hand at the face
  must be drawn after it (Godot cutout: fix depth with Z/"behind parent" without breaking the hierarchy).
  `guy()` now does this automatically when the hand is at the face, and keeps raised hands behind the head so the
  order never flickers at the top of a swing.

## 7. Overlap, follow-through, arcs (making it read as alive)

Disney's principles that matter for rigs: **arcs** (limbs rotate about joints, so hands travel in curves),
**slow in/slow out**, **follow-through and overlapping action** (hair, cloth, loose limbs lag the body and settle),
**timing** (frames = weight), **squash and stretch with constant volume**.
For lag/settle use a **critically damped spring** solved exactly (Holden, "Spring-It-On"): halflife sets the lag,
it never overshoots or goes unstable at big time steps. `rigsafe.spring_follow` re-simulates a short window so
frames can render in any order.

## 8. Skinning and sculpting for deformation (advanced: when we sculpt real meshes)

- **Linear blend skinning** collapses at bends and "candy-wraps" on twist (elbow, wrist). **Dual quaternion
  skinning** keeps volume on twist but can bulge on bends; Maya's weight-blended mode mixes the two per joint
  (Autodesk smooth-skinning docs).
- **Twist bones:** split the forearm/upper-arm twist over helper bones (e.g. 50% at mid-forearm); "untwist" upper
  arms and thighs so they bend without spinning (Cascadeur twist bones).
- **Corrective shapes / pose-space deformation:** sculpt fixes at problem poses (elbow bent, arm raised) and blend
  them by pose distance with RBF interpolation (PSD course notes).
- **Topology for joints:** circular edge loops at joints, long flow along limbs; elbows/knees 2-3 tight rings on the
  crease side and 1-2 broader on the stretch side; shoulders: loops around the deltoid plus an extra stack for the
  clavicle; wrists/ankles: concentric rings either side of the pivot; neck: collar-like loops, no T-junctions.
- **Sculpt big to small:** block primary masses at low subdivision, set proportions from bony landmarks (knuckles,
  elbow, knee, scapula/trapezius triangles), then refine; the elbow's two motions (flex and forearm roll) decide
  how the forearm muscles wrap.

- **Clothes over a skinned body (our rules, learned the hard way):**
  1. *Layer by construction.* Each layer is built from the one under it plus a gap: jeans hem = max(leg, shoe collar
     + 6 mm); shirt hem = max(shirt, jeans + 13 mm). In the rest pose nothing touches, so nothing can start inside.
  2. *Shared weights.* Every clothing layer takes its skin weights from the same body (torso + arms + legs), and the
     layers that overlap use the same blend curve (shoe collar and jeans hem both ride foot->shin on one curve). Layers
     with different weights drift apart in poses and poke through each other.
  3. *Cloth bridges, skin carves.* Fabric is the body blended softly (large smooth-min) and never closer than 7 mm
     to the exact body, so it drapes over the small forms (no shrink-wrapped ribs or "turtle shell" shoulder blades).
  4. *Only open cloth needs a back face.* The shirt is a 5 mm shell only near the neck opening; elsewhere it is solid
     (thin shells over the whole torso break into holes when decimated).
  5. *Neck to chest is a slow hand-off* (7 cm blend above the collarbones), so turning the head never folds neck skin
     through the collarbones or the collar.
  6. Check with `web/clothcheck.sh` (walk + flexed foot, deep crouch, head turn + shrug, twist + leg up).

## 9. Our checklist (enforced)

1. Pose in local angles; root carries the tumble.  2. Soft-limit every joint, parent first.  3. Hinges one way.
4. IK only through `ik_arm` / limit-aware solvers, angles blended for moves.  5. Blend the short way; never warp a
flail's clock; bounded `flail`.  6. Capsule collision + push-out; hand at face drawn over the head.
7. Run the checker: `python3 studio/toon/shorts/rigcheck.py <name> <work dir>` (house Shorts, ~15 s) or
`node rigcheck3d.mjs "scene.html?level=2" out.json && python3 rigcheck3d.py out.json` (3D).
8. For the 3D guy, also `bash web/clothcheck.sh /tmp/cc` and look at the 3 sheets for cloth poking through.

## Sources

- [WikEM: range of motion by joint](https://wikem.org/wiki/Joint_ROM_(Table)) (Luttgens & Hamilton)
- [Normal scapulohumeral rhythm](https://boneandspine.com/normal-scapulohumeral-rhythm/)
- [Unity Character Joint (twist/swing limits, springs)](https://docs.unity3d.com/Manual/class-CharacterJoint.html)
- [Maya: troubleshoot IK joint flipping](https://help.autodesk.com/cloudhelp/2017/ENU/Maya/files/GUID-AD60045C-67FE-4367-8AB7-C5F26485740B.htm)
- [Maya rigging wiki: rotation order / joint orient](https://www.sites.google.com/site/mayariggingwiki/rigging-notes/rig-fundamentals/rotation-order)
- [FABRIK paper (Aristidou & Lasenby)](https://perso.liris.cnrs.fr/alexandre.meyer/teaching/master_charanim/M2_3_video_IK_Procedurale/FABRIK.pdf), [project page](https://www.andreasaristidou.com/FABRIK)
- [Slerp and the double cover](https://en.wikipedia.org/wiki/Spherical_linear_interpolation)
- [Euler filter](https://en.wikipedia.org/wiki/Euler_filter)
- [Holden: Unrolling Rotations](https://theorangeduck.com/page/unrolling-rotations)
- [Holden: Spring-It-On (critically damped springs)](https://theorangeduck.com/page/spring-roll-call)
- [NAO self-collision avoidance (capsule model)](https://fileadmin.cs.lth.se/cs/Education/MMKN30/Nao/download/Documentation/naoqi/motion/reflexes-collision-avoidance.html)
- [Godot cutout animation (pivots, hierarchy, draw order)](https://github.com/godotengine/godot-docs/blob/stable/./tutorials/animation/cutout_animation.rst)
- [Disney's 12 principles](https://www.simonwhatley.co.uk/writing/disney-12-basic-principles-of-animation/)
- [Maya smooth skinning methods](https://help.autodesk.com/cloudhelp/ENU/MayaCRE-CharacterAnimation/files/GUID-630C335C-B63E-4F2E-A4A4-AEA1DD00B0D6.htm)
- [Pose space deformation](https://imagine.inrialpes.fr/people/Francois.Faure/htmlCourses/PoseSpaceDeformation.html)
- [Cascadeur: twist bones](https://cascadeur.com/help/rig/advanced_rigging/advanced_rigging_techniques/twist_bones)
- [Deformation-ready joint topology](https://novedge.com/blogs/design-news/zbrush-tip-deformation-ready-joint-topology-with-zremesher)
- [Sculpting anatomy: masses first](https://www.creativebloq.com/3d/anatomy-part-2-sculpting-masses-81412508)
