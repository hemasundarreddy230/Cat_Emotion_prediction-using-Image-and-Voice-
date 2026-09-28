from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random

from emotion_detection.models import CatProfile, EmotionPrediction, AIConversation

# Enhanced Cat-focused AI responses with comprehensive guidance
CAT_RESPONSES = {
    'greeting': [
        "🐱 Hello! I'm your dedicated cat care AI assistant. I specialize in feline health, behavior, and care. How can I help you with your cat today?",
        "Meow! I'm here exclusively for cat-related questions. Whether it's health, behavior, or care tips, I'm ready to help! 🐾",
        "Purr-fect! I'm your cat care specialist AI. Ask me anything about feline health, emotions, diet, or behavior!"
    ],
    'emotion_happy': [
        "🐱 Wonderful! A happy cat shows contentment through purring, kneading, slow blinking, and relaxed body posture. This indicates excellent care! Signs of happiness include: active play, good appetite, seeking affection, and confident exploration. Keep providing that loving environment with consistent routines, interactive play sessions, and plenty of affection.",
        "😸 Happy cats are healthy cats! Signs include playful behavior, good appetite, and seeking affection. To maintain this happiness: continue regular play sessions (10-15 minutes twice daily), provide vertical spaces like cat trees, maintain clean litter boxes, and offer variety in toys. A content cat often purrs, head-butts, and shows their belly - all signs of trust and security.",
        "🐾 Excellent! Happy feline emotions suggest your cat feels secure, loved, and well-cared for. Continue your great cat parenting! Happy cats typically: eat regularly, groom themselves properly, engage in play, seek social interaction, and maintain normal sleep patterns. Keep up the excellent work with consistent care, environmental enrichment, and lots of love!"
    ],
    'emotion_sad': [
        "😿 I understand your concern about your cat appearing sad. Cat sadness can manifest as: decreased appetite, hiding more than usual, reduced grooming, lethargy, or changes in vocalization. Here's what you should do:\n\n🔍 **Immediate Assessment:**\n• Check for physical signs of illness (eating, drinking, litter box use)\n• Note any recent changes (new pets, moving, schedule changes)\n• Observe if they're still responsive to favorite treats or toys\n\n💡 **Helpful Actions:**\n• Increase gentle interaction and petting sessions\n• Provide cozy hiding spots with soft blankets\n• Try interactive play with feather wands or laser pointers\n• Consider calming pheromone diffusers (Feliway)\n• Maintain consistent feeding and play schedules\n\n⚠️ **When to See a Vet:**\nIf sadness persists beyond 2-3 days, or if accompanied by appetite loss, hiding constantly, or changes in bathroom habits, please consult your veterinarian to rule out medical issues.",
        "🐱 Cat sadness often indicates stress, boredom, illness, or environmental changes. Let me help you understand and address this:\n\n📋 **Common Causes:**\n• Environmental changes (new home, furniture, people)\n• Boredom from lack of mental stimulation\n• Social stress (new pets, conflicts with other cats)\n• Medical issues (pain, illness, aging)\n• Seasonal changes or weather\n\n🎯 **Solutions to Try:**\n• **Enrichment:** Puzzle feeders, cat trees, window perches\n• **Play Therapy:** 15-20 minutes of interactive play daily\n• **Comfort:** Create quiet safe spaces with familiar scents\n• **Routine:** Maintain consistent feeding and interaction times\n• **Social:** Spend quality one-on-one time together\n\n🏥 **Monitor For:** Changes in eating, drinking, litter box use, or if sadness worsens. These could indicate medical issues requiring veterinary attention.",
        "😔 When cats seem sad, they need extra care and attention. Here's a comprehensive approach:\n\n🧠 **Understanding Cat Depression:**\nCats can experience depression-like symptoms due to: loss of companion, major life changes, lack of stimulation, or underlying health issues.\n\n🎮 **Mental Stimulation Ideas:**\n• Rotate toys weekly to maintain novelty\n• Hide treats around the house for 'hunting'\n• Provide puzzle feeders and treat-dispensing toys\n• Create vertical spaces for climbing and perching\n• Consider a companion cat if yours seems lonely\n\n💝 **Emotional Support:**\n• Gentle brushing sessions (if they enjoy it)\n• Soft talking and slow blinking to show affection\n• Respect their space while staying available\n• Use positive reinforcement with treats and praise\n• Consider calming music designed for cats\n\n⏰ **Timeline:** Most situational sadness improves within 1-2 weeks with proper care. If not, consult your vet for potential medical causes or behavioral therapy options."
    ],
    'emotion_angry': [
        "😾 Angry cats show flattened ears, hissing, swishing tails, or aggressive postures. Understanding and addressing cat anger safely:\n\n🚨 **Immediate Safety:**\n• Give your cat space - don't force interaction\n• Avoid punishment, which escalates aggression\n• Remove triggers if identifiable\n• Speak softly and move slowly\n\n🔍 **Common Triggers:**\n• Territorial disputes with other pets\n• Fear or feeling cornered\n• Overstimulation during petting\n• Pain or medical discomfort\n• Changes in environment or routine\n\n🛠️ **Solutions:**\n• Provide multiple escape routes and hiding spots\n• Use positive reinforcement training\n• Gradually reintroduce triggers at low intensity\n• Consider pheromone diffusers for calming\n• Ensure each cat has their own resources (food, water, litter)\n\n⚕️ **When to Seek Help:** If aggression is sudden, severe, or accompanied by other behavioral changes, consult your vet to rule out pain or medical issues.",
        "🐱 Cat anger often stems from stress, fear, pain, or territorial issues. Here's how to help your angry cat:\n\n📊 **Types of Cat Aggression:**\n• **Fear-based:** Defensive, trying to escape\n• **Territorial:** Protecting resources or space\n• **Redirected:** Frustrated by something else\n• **Play:** Overstimulated during interaction\n• **Medical:** Pain-induced defensive behavior\n\n🎯 **Management Strategies:**\n• **Environment:** Create calm, predictable spaces\n• **Resources:** Provide multiple food/water stations\n• **Play:** Channel energy into appropriate outlets\n• **Routine:** Maintain consistent daily schedules\n• **Patience:** Allow time for trust rebuilding\n\n🏠 **Home Modifications:**\n• Install cat trees for vertical territory\n• Use baby gates to create separate spaces\n• Provide hiding boxes in each room\n• Consider calming supplements (consult vet first)\n\n📞 **Professional Help:** Contact a certified cat behaviorist if aggression persists or escalates.",
        "😤 Aggressive feline behavior needs careful, patient handling. Never punish an angry cat - this increases fear and aggression:\n\n🧘 **De-escalation Techniques:**\n• Remain calm and speak softly\n• Avoid direct eye contact (seen as threatening)\n• Move slowly and predictably\n• Give the cat control over interactions\n• Use treats to create positive associations\n\n🔄 **Behavior Modification:**\n• **Counter-conditioning:** Pair triggers with good things\n• **Desensitization:** Gradual exposure to triggers\n• **Environmental management:** Remove or modify triggers\n• **Positive reinforcement:** Reward calm behavior\n\n🏥 **Medical Considerations:**\nSudden aggression can indicate: arthritis pain, dental issues, hyperthyroidism, or neurological problems. A vet exam is crucial for sudden behavioral changes.\n\n⏱️ **Recovery Timeline:** With consistent management, most cats show improvement in 2-4 weeks, though some cases may take months of patient work."
    ],
    'emotion_scared': [
        "😨 Scared cats need patience and understanding. Fear responses include hiding, dilated pupils, freezing, or attempting to escape:\n\n🛡️ **Creating Safety:**\n• Provide multiple hiding spots (boxes, cat caves, under furniture)\n• Keep a consistent, quiet environment\n• Avoid forcing interactions\n• Let your cat approach you on their terms\n• Use soft, reassuring voice tones\n\n🎯 **Common Fear Triggers:**\n• Loud noises (thunderstorms, fireworks, construction)\n• New people or animals\n• Veterinary visits or car rides\n• Changes in environment\n• Past traumatic experiences\n\n💡 **Building Confidence:**\n• **Gradual exposure:** Start with trigger at low intensity/distance\n• **Positive associations:** Pair scary things with treats/play\n• **Safe spaces:** Ensure escape routes are always available\n• **Routine:** Maintain predictable daily schedules\n• **Patience:** Never rush the process\n\n🌿 **Natural Calming Aids:**\n• Feliway pheromone diffusers\n• Calming music for cats\n• Anxiety wraps or thunder shirts\n• Herbal supplements (vet-approved only)",
        "🐱 Fearful cats require special care and patience. Here's a comprehensive approach to helping scared cats:\n\n🏠 **Environmental Setup:**\n• **Vertical spaces:** Cat trees, shelves for elevated hiding\n• **Multiple exits:** Never corner a scared cat\n• **Quiet zones:** Areas away from household activity\n• **Familiar scents:** Use their bedding or your worn clothing\n• **Consistent lighting:** Avoid sudden bright lights\n\n🎮 **Confidence-Building Activities:**\n• **Interactive play:** Use wand toys to build positive experiences\n• **Treat training:** Teach simple commands with rewards\n• **Puzzle feeders:** Mental stimulation builds confidence\n• **Clicker training:** Positive reinforcement techniques\n\n📅 **Gradual Socialization:**\n• Start with brief, positive interactions\n• Let the cat set the pace\n• Use high-value treats during exposure\n• Never force physical contact\n• Celebrate small victories\n\n⚕️ **When to Consult Professionals:**\n• Fear prevents normal activities (eating, using litter box)\n• No improvement after 4-6 weeks of consistent work\n• Fear escalates to aggression\n• Consider anti-anxiety medication for severe cases",
        "😰 Cat fear responses require understanding and systematic desensitization. Here's how to help your scared cat:\n\n🧠 **Understanding Fear in Cats:**\n• Cats have strong flight responses\n• Fear memories can be long-lasting\n• Genetics and early socialization affect fear responses\n• Medical issues can increase fearfulness\n\n🎯 **Systematic Desensitization Plan:**\n1. **Identify triggers:** Note what specifically scares your cat\n2. **Create hierarchy:** List triggers from least to most scary\n3. **Start small:** Begin with mildest version of trigger\n4. **Pair with positives:** Use treats, play, or affection\n5. **Progress gradually:** Only advance when cat is comfortable\n6. **Be consistent:** Daily short sessions work better than long ones\n\n🏆 **Success Indicators:**\n• Relaxed body posture around former triggers\n• Willingness to explore new areas\n• Normal eating and litter box use\n• Seeking interaction with family members\n• Playing and showing curiosity\n\n⏰ **Timeline:** Fear recovery varies greatly - some cats improve in weeks, others need months of patient work."
    ],
    'health': [
        "🏥 Cat health requires vigilant observation and regular veterinary care. Here's comprehensive health guidance:\n\n⚠️ **Emergency Signs (Seek immediate vet care):**\n• Difficulty breathing or open-mouth breathing\n• Inability to urinate or defecate\n• Severe lethargy or unresponsiveness\n• Repeated vomiting or diarrhea\n• Signs of severe pain (hiding, aggression, vocalization)\n• Pale gums or difficulty walking\n\n📋 **Daily Health Monitoring:**\n• **Appetite:** Note changes in eating or drinking\n• **Litter box:** Monitor frequency and consistency\n• **Behavior:** Watch for hiding, aggression, or lethargy\n• **Grooming:** Check if they're maintaining cleanliness\n• **Mobility:** Observe walking, jumping, and movement\n\n🗓️ **Preventive Care Schedule:**\n• **Annual exams:** For cats under 7 years\n• **Bi-annual exams:** For senior cats (7+ years)\n• **Vaccinations:** As recommended by your vet\n• **Dental care:** Regular teeth cleaning and dental treats\n• **Parasite prevention:** Flea, tick, and worm prevention\n\n💊 **Home Health Support:**\n• Maintain ideal weight through proper diet\n• Provide fresh water daily\n• Keep environment stress-free\n• Regular grooming and nail trims",
        "🐱 Comprehensive cat health management involves prevention, observation, and prompt veterinary care:\n\n🔍 **Health Assessment Checklist:**\n• **Eyes:** Clear, bright, no discharge or cloudiness\n• **Ears:** Clean, no odor, wax, or excessive scratching\n• **Nose:** Cool, moist, no discharge\n• **Mouth:** Pink gums, no bad breath, white teeth\n• **Coat:** Shiny, no bald patches, parasites, or excessive shedding\n• **Weight:** Maintain ideal body condition (ribs felt but not seen)\n\n🏠 **Creating a Healthy Environment:**\n• **Clean litter boxes:** Scoop daily, change weekly\n• **Fresh water:** Multiple sources, cleaned regularly\n• **Safe spaces:** Remove toxic plants and hazardous items\n• **Temperature control:** Comfortable climate year-round\n• **Stress reduction:** Consistent routines and calm environment\n\n📊 **Age-Specific Health Needs:**\n• **Kittens (0-1 year):** Frequent vet visits, vaccinations, spay/neuter\n• **Adults (1-7 years):** Annual checkups, dental care, weight management\n• **Seniors (7+ years):** Bi-annual exams, blood work, arthritis monitoring\n\n🚨 **Common Health Issues to Watch:**\n• Urinary tract problems (especially in males)\n• Dental disease (affects 80% of cats by age 3)\n• Obesity (affects 60% of house cats)\n• Kidney disease (common in seniors)\n• Hyperthyroidism (senior cats)",
        "⚕️ Proactive cat health care prevents many serious conditions. Here's your complete health guide:\n\n🎯 **Nutrition for Health:**\n• **High-quality protein:** Cats need 26% minimum protein\n• **Proper hydration:** Wet food helps prevent urinary issues\n• **Age-appropriate food:** Kitten, adult, or senior formulas\n• **Weight management:** Obesity leads to diabetes, arthritis\n• **Avoid toxic foods:** Chocolate, onions, garlic, grapes, xylitol\n\n🏃 **Exercise and Mental Health:**\n• **Daily play:** 10-15 minutes of active play twice daily\n• **Environmental enrichment:** Cat trees, puzzle feeders, toys\n• **Mental stimulation:** Hunting games, treat puzzles\n• **Social interaction:** Quality time with family members\n\n🧼 **Hygiene and Grooming:**\n• **Brushing:** Daily for long-haired, weekly for short-haired\n• **Nail trims:** Every 2-3 weeks for indoor cats\n• **Dental care:** Daily brushing ideal, dental treats minimum\n• **Ear cleaning:** Weekly check, clean if needed\n\n📱 **Health Tracking:**\n• Keep vaccination records updated\n• Note any behavioral or physical changes\n• Track eating, drinking, and litter box habits\n• Photograph any concerning symptoms for vet visits\n• Maintain relationship with trusted veterinarian"
    ],
    'diet': [
        "🍽️ Proper cat nutrition is crucial for health and longevity. Cats are obligate carnivores with specific dietary needs:\n\n🥩 **Essential Nutritional Requirements:**\n• **Protein:** Minimum 26% (dry matter basis), ideally 35-45%\n• **Taurine:** Essential amino acid (deficiency causes heart/eye problems)\n• **Arachidonic acid:** Essential fatty acid found only in animal tissue\n• **Vitamin A:** Must come from animal sources (can't convert from beta-carotene)\n• **Niacin:** Cannot synthesize from tryptophan like other animals\n\n⚠️ **Toxic Foods to Avoid:**\n• **Chocolate:** Contains theobromine (toxic to cats)\n• **Onions/Garlic:** Damages red blood cells\n• **Grapes/Raisins:** Can cause kidney failure\n• **Xylitol:** Artificial sweetener causes hypoglycemia\n• **Alcohol:** Even small amounts are dangerous\n• **Caffeine:** Found in coffee, tea, energy drinks\n\n🍽️ **Feeding Guidelines:**\n• **Portion control:** Follow package guidelines, adjust for activity\n• **Multiple small meals:** 2-4 meals daily better than free-feeding\n• **Fresh water:** Always available, changed daily\n• **Consistent schedule:** Helps with digestion and behavior\n\n🏥 **Special Dietary Considerations:**\n• **Kittens:** Need kitten formula until 12 months\n• **Seniors:** May need easily digestible, higher-quality protein\n• **Medical conditions:** Kidney, diabetes, allergies require special diets",
        "🐱 Optimal cat nutrition supports health, energy, and longevity. Here's comprehensive feeding guidance:\n\n🏆 **Choosing Quality Cat Food:**\n• **First ingredient:** Named meat (chicken, salmon, beef)\n• **AAFCO statement:** Ensures nutritional adequacy\n• **Life stage appropriate:** Kitten, adult, or senior formulas\n• **Avoid fillers:** Excessive corn, wheat, or by-products\n• **Consider wet food:** Higher moisture content supports urinary health\n\n📊 **Feeding Schedule by Age:**\n• **Kittens (8-12 weeks):** 4 meals daily, free-choice dry food\n• **Young cats (3-6 months):** 3 meals daily\n• **Adults (6 months+):** 2 meals daily, measured portions\n• **Seniors (7+ years):** 2-3 smaller meals, easier to digest\n\n💧 **Hydration Importance:**\n• Cats have low thirst drive (desert ancestors)\n• Wet food provides 70-80% moisture content\n• Fresh water should always be available\n• Consider water fountains to encourage drinking\n• Monitor for increased/decreased water consumption\n\n🎯 **Weight Management:**\n• **Ideal body condition:** Ribs felt but not visible\n• **Portion control:** Measure food, don't free-feed\n• **Treat limits:** No more than 10% of daily calories\n• **Exercise:** Combine diet with active play\n• **Regular weigh-ins:** Monthly monitoring prevents obesity",
        "🥘 Advanced cat nutrition for optimal health and addressing common dietary challenges:\n\n🔄 **Food Transition Protocol:**\n• **Days 1-2:** 75% old food, 25% new food\n• **Days 3-4:** 50% old food, 50% new food\n• **Days 5-6:** 25% old food, 75% new food\n• **Day 7+:** 100% new food\n• **Monitor:** Watch for digestive upset during transition\n\n🏥 **Therapeutic Diets (Vet-Prescribed):**\n• **Urinary health:** Low magnesium, controlled pH\n• **Kidney disease:** Reduced phosphorus, high-quality protein\n• **Diabetes:** High protein, low carbohydrate\n• **Food allergies:** Limited ingredient or hydrolyzed protein\n• **Weight management:** Reduced calories, increased fiber\n\n🍖 **Raw Diet Considerations:**\n• **Benefits:** High protein, minimal processing\n• **Risks:** Bacterial contamination, nutritional imbalances\n• **Safety:** Proper handling, balanced formulation essential\n• **Consultation:** Work with veterinary nutritionist\n\n🎮 **Feeding Enrichment:**\n• **Puzzle feeders:** Slow eating, mental stimulation\n• **Food hiding:** Encourages natural hunting behavior\n• **Multiple stations:** Reduces competition in multi-cat homes\n• **Elevated bowls:** May help with digestion in some cats\n\n📈 **Monitoring Nutritional Success:**\n• Healthy weight maintenance\n• Shiny coat and healthy skin\n• Good energy levels\n• Normal litter box habits\n• Regular veterinary checkups confirm health"
    ],
    'behavior': [
        "🐾 Understanding cat behavior helps build stronger bonds and address issues effectively:\n\n😺 **Normal Cat Behaviors Explained:**\n• **Kneading:** Shows contentment, mimics nursing behavior\n• **Head butting/rubbing:** Scent marking, showing affection\n• **Purring:** Usually contentment, sometimes self-soothing when stressed\n• **Slow blinking:** Sign of trust and affection ('cat kisses')\n• **Scratching:** Territory marking, claw maintenance, stretching\n• **Hunting play:** Natural instinct, needs outlet through interactive toys\n\n📊 **Body Language Guide:**\n• **Tail up:** Confident, happy, greeting\n• **Tail puffed:** Scared, defensive, or excited\n• **Tail swishing:** Agitated, overstimulated, or focused\n• **Ears forward:** Alert, interested, content\n• **Ears flattened:** Scared, angry, or defensive\n• **Slow blinking:** Relaxed, trusting\n• **Dilated pupils:** Excited, scared, or overstimulated\n\n🎯 **Addressing Common Behavior Issues:**\n• **Inappropriate elimination:** Rule out medical issues first\n• **Excessive vocalization:** May indicate pain, cognitive issues, or attention-seeking\n• **Destructive scratching:** Provide appropriate scratching posts\n• **Aggression:** Identify triggers, provide safe spaces\n• **Hiding:** Ensure adequate hiding spots, check for stressors",
        "🐱 Comprehensive cat behavior understanding for better human-feline relationships:\n\n🧠 **Cat Psychology Basics:**\n• **Territorial nature:** Cats need defined spaces and resources\n• **Routine-oriented:** Thrive on predictable schedules\n• **Independent but social:** Need interaction on their terms\n• **Prey drive:** Hunting instincts remain strong in domestic cats\n• **Scent communication:** Use pheromones and scent marking extensively\n\n🏠 **Environmental Behavior Factors:**\n• **Vertical territory:** Cats feel safer with high perches\n• **Multiple resources:** Prevent competition (food, water, litter, toys)\n• **Hiding spots:** Essential for security and stress management\n• **Window access:** Visual stimulation from outdoor activity\n• **Consistent layout:** Avoid frequent furniture rearrangement\n\n🎮 **Enrichment for Behavioral Health:**\n• **Interactive play:** 10-15 minutes, 2-3 times daily\n• **Puzzle feeders:** Mental stimulation during meals\n• **Rotating toys:** Maintain novelty and interest\n• **Cat TV:** Bird/fish videos for visual entertainment\n• **Catnip/silvervine:** Natural mood enhancers (not all cats respond)\n\n🔄 **Behavior Modification Techniques:**\n• **Positive reinforcement:** Reward desired behaviors\n• **Environmental management:** Remove triggers when possible\n• **Redirection:** Guide unwanted behavior to appropriate outlets\n• **Consistency:** All family members use same approach\n• **Patience:** Behavior change takes time and repetition",
        "😺 Advanced feline behavior analysis and problem-solving strategies:\n\n🎯 **Specific Behavior Solutions:**\n\n**Litter Box Issues:**\n• **Medical check:** Rule out UTI, constipation, arthritis\n• **Box cleanliness:** Scoop daily, change litter weekly\n• **Location:** Quiet, accessible, away from food\n• **Number:** One per cat plus one extra\n• **Litter type:** Unscented, clumping preferred by most cats\n\n**Excessive Meowing:**\n• **Medical causes:** Hyperthyroidism, cognitive dysfunction, pain\n• **Attention-seeking:** Don't reward with attention during excessive vocalization\n• **Routine needs:** Ensure feeding, play, and attention schedules are met\n• **Environmental stressors:** Identify and address sources of anxiety\n\n**Furniture Scratching:**\n• **Appropriate outlets:** Multiple scratching posts in preferred areas\n• **Post preferences:** Vertical/horizontal, different textures\n• **Deterrents:** Double-sided tape, aluminum foil on furniture\n• **Positive reinforcement:** Reward using appropriate scratching areas\n• **Nail maintenance:** Regular trims reduce damage\n\n🏥 **When to Consult Professionals:**\n• Sudden behavior changes (may indicate medical issues)\n• Aggression toward people or other pets\n• Persistent litter box problems\n• Excessive hiding or fearfulness\n• Destructive behaviors not responding to management\n\n📚 **Ongoing Behavior Management:**\n• Regular play sessions prevent many behavior problems\n• Environmental enrichment reduces stress and boredom\n• Consistent routines provide security\n• Positive human-cat interactions build trust\n• Early intervention prevents problems from becoming habits"
    ],
    'litter': [
        "🚽 Proper litter box management is crucial for cat health and household harmony:\n\n📏 **Litter Box Setup Essentials:**\n• **Number:** One per cat plus one extra (minimum)\n• **Size:** Large enough for cat to turn around comfortably\n• **Depth:** 2-3 inches of litter (most cats prefer shallow)\n• **Location:** Quiet, accessible, away from food and water\n• **Type:** Open boxes preferred by most cats (better ventilation)\n\n🧹 **Maintenance Schedule:**\n• **Daily:** Scoop waste, check litter level\n• **Weekly:** Complete litter change, wash box with mild soap\n• **Monthly:** Deep clean with enzymatic cleaner\n• **As needed:** Add fresh litter to maintain 2-3 inch depth\n\n🏥 **Health Monitoring Through Litter Box:**\n• **Frequency:** Normal cats urinate 2-4 times daily\n• **Consistency:** Firm, formed stools indicate good health\n• **Color changes:** Blood, unusual colors warrant vet consultation\n• **Straining:** Difficulty urinating/defecating needs immediate attention\n• **Accidents:** Sudden litter box avoidance often indicates medical issues\n\n⚠️ **Common Problems and Solutions:**\n• **Box avoidance:** Check for medical issues, cleanliness, location\n• **Tracking:** Use mats, consider different litter types\n• **Odor:** Increase scooping frequency, use odor-controlling litter\n• **Multiple cats:** Ensure adequate number of boxes, separate locations",
        "🐱 Comprehensive litter box management for optimal cat health and behavior:\n\n🎯 **Litter Type Selection:**\n• **Clay clumping:** Most popular, easy scooping, good odor control\n• **Non-clumping clay:** Absorbent, economical, needs frequent changing\n• **Crystal/silica:** Excellent odor control, low dust, longer lasting\n• **Natural/biodegradable:** Corn, wheat, pine - eco-friendly options\n• **Unscented preferred:** Most cats dislike artificial fragrances\n\n🏠 **Multi-Cat Household Management:**\n• **Separate resources:** Each cat should have access to their own box\n• **Strategic placement:** Boxes on different floors/areas of home\n• **Individual preferences:** Some cats prefer specific litter types\n• **Territorial considerations:** Prevent guarding behavior at boxes\n• **Extra maintenance:** More frequent scooping and cleaning needed\n\n🔍 **Troubleshooting Litter Box Issues:**\n\n**Medical Causes (Vet consultation needed):**\n• Urinary tract infections or blockages\n• Digestive issues (diarrhea, constipation)\n• Arthritis making box access difficult\n• Cognitive dysfunction in senior cats\n\n**Environmental Causes:**\n• Box too dirty or strong chemical odors\n• Location too noisy, busy, or hard to access\n• Negative associations (being startled while using box)\n• Litter type changes or strong fragrances\n• Stress from household changes\n\n**Behavioral Solutions:**\n• **Re-training:** Confine to small area with box until habits re-establish\n• **Positive associations:** Treats and praise near (not in) litter area\n• **Clean accidents thoroughly:** Use enzymatic cleaners to remove odors\n• **Multiple options:** Offer different litter types to find preference",
        "📦 Advanced litter box strategies for challenging situations and optimal management:\n\n🎯 **Special Circumstances:**\n\n**Senior Cats (7+ years):**\n• **Lower sides:** Easier entry for arthritic cats\n• **More locations:** Reduce travel distance to boxes\n• **Softer litter:** Gentler on sensitive paws\n• **Night lights:** Help with vision changes\n• **Regular monitoring:** Age-related health issues affect elimination\n\n**Kittens:**\n• **Shallow boxes:** Easy access for small cats\n• **Non-clumping litter:** Safer if ingested during learning\n• **Frequent cleaning:** Accidents common during training\n• **Multiple small boxes:** Easier to find when needed\n• **Gradual transition:** From paper/pellets to adult litter\n\n**Medical Conditions:**\n• **Diabetes:** May need larger boxes due to increased urination\n• **Kidney disease:** More frequent box changes needed\n• **Arthritis:** Ramps or lower-sided boxes for easier access\n• **Declawed cats:** Softer litter types (paper, corn-based)\n• **Post-surgery:** Temporary paper litter to prevent infection\n\n🧪 **Advanced Maintenance:**\n• **Enzymatic cleaners:** Break down odor-causing bacteria\n• **UV lights:** Detect hidden urine spots for thorough cleaning\n• **Air purifiers:** Help control litter area odors\n• **Automatic boxes:** Consider for busy households (introduce gradually)\n• **Litter tracking mats:** Reduce litter spread throughout home\n\n📊 **Success Metrics:**\n• Consistent daily use of litter boxes\n• No accidents outside boxes\n• Normal elimination frequency and consistency\n• Cat appears comfortable and unstressed when using box\n• Household odor remains manageable with regular maintenance"
    ],
    'play': [
        "🎾 Play is essential for cat physical and mental health. Here's how to provide optimal play experiences:\n\n🎯 **Benefits of Regular Play:**\n• **Physical health:** Maintains healthy weight, muscle tone, flexibility\n• **Mental stimulation:** Prevents boredom, reduces behavioral problems\n• **Stress relief:** Natural outlet for energy and hunting instincts\n• **Bonding:** Strengthens relationship between cat and owner\n• **Sleep quality:** Tired cats sleep better and are less active at night\n\n🕐 **Optimal Play Schedule:**\n• **Frequency:** 2-3 sessions daily, 10-15 minutes each\n• **Timing:** Before meals (mimics hunt-eat-sleep cycle)\n• **Evening play:** Helps reduce nighttime activity\n• **Consistency:** Regular schedule helps establish routine\n• **Individual needs:** Adjust based on age, health, and energy level\n\n🎮 **Types of Interactive Play:**\n• **Wand toys:** Feathers, strings, mice - simulate prey movement\n• **Laser pointers:** Great exercise, but always end with physical 'catch'\n• **Ball games:** Ping pong balls, crinkle balls for solo play\n• **Puzzle toys:** Treat-dispensing toys provide mental challenge\n• **Catnip toys:** Natural stimulant for play (60-70% of cats respond)\n\n⚠️ **Play Safety:**\n• Supervise string/ribbon toys to prevent ingestion\n• Check toys regularly for damage or loose parts\n• Store small toys safely when not supervised\n• Never leave laser pointer unattended\n• Rotate toys weekly to maintain interest",
        "🐱 Comprehensive play strategies for cats of all ages and activity levels:\n\n🏆 **Age-Appropriate Play:**\n\n**Kittens (8 weeks - 1 year):**\n• **High energy:** 4-6 short play sessions daily\n• **Social play:** Gentle wrestling with littermates or humans\n• **Exploration toys:** Balls, tunnels, climbing structures\n• **Teething toys:** Soft toys for chewing and carrying\n• **Safety first:** Avoid small parts that could be swallowed\n\n**Adult Cats (1-7 years):**\n• **Structured play:** 2-3 sessions, 15-20 minutes each\n• **Hunting simulation:** Wand toys moved like real prey\n• **Variety:** Rotate different types of toys and games\n• **Challenge level:** Adjust difficulty to maintain interest\n• **Solo play options:** Toys available when owners aren't home\n\n**Senior Cats (7+ years):**\n• **Gentle play:** Shorter sessions, less intense movement\n• **Mental stimulation:** Puzzle feeders, treat-hiding games\n• **Comfort considerations:** Soft surfaces, easy-to-catch toys\n• **Health monitoring:** Watch for signs of fatigue or discomfort\n• **Adapted toys:** Larger, easier-to-see toys for vision changes\n\n🎯 **Environmental Enrichment:**\n• **Vertical spaces:** Cat trees, shelves, perches\n• **Hiding spots:** Boxes, tunnels, cat caves\n• **Window entertainment:** Bird feeders, outdoor views\n• **Scratching variety:** Posts, pads, different textures\n• **Sensory experiences:** Different textures, sounds, scents",
        "🎮 Advanced play techniques and enrichment strategies for optimal feline wellness:\n\n🧠 **Mental Stimulation Games:**\n• **Food puzzles:** Hide treats in puzzle feeders, toilet paper rolls\n• **Hunting games:** Hide food around house for 'foraging'\n• **Training sessions:** Teach tricks using positive reinforcement\n• **Rotation system:** Change available toys every few days\n• **DIY enrichment:** Cardboard boxes, paper bags, toilet paper rolls\n\n🎯 **Behavior-Specific Play Solutions:**\n\n**Overweight Cats:**\n• **Gradual increase:** Start with 5-minute sessions, build endurance\n• **Low-impact play:** Wand toys at ground level, rolling balls\n• **Food motivation:** Use treats and meals as play rewards\n• **Multiple short sessions:** Better than one long session\n• **Monitor closely:** Watch for overexertion, provide water breaks\n\n**Shy/Fearful Cats:**\n• **Solo play first:** Leave toys out for independent exploration\n• **Distance play:** Start with toys far from human, gradually get closer\n• **Quiet toys:** Avoid loud, startling sounds initially\n• **Safe spaces:** Play in cat's preferred hiding areas\n• **Patience:** Let cat set the pace, don't force interaction\n\n**High-Energy Cats:**\n• **Intense sessions:** Longer, more vigorous play periods\n• **Multiple types:** Combine different play styles in one session\n• **Obstacle courses:** Create climbing and jumping challenges\n• **Companion play:** Consider second cat for social play\n• **Evening focus:** Tire out before bedtime to reduce night activity\n\n🏥 **Health Benefits Tracking:**\n• **Weight management:** Regular play helps maintain healthy weight\n• **Muscle tone:** Active cats maintain better physical condition\n• **Joint health:** Movement keeps joints flexible and strong\n• **Mental health:** Reduces anxiety, depression, and behavioral issues\n• **Sleep quality:** Well-exercised cats have better sleep patterns\n\n📊 **Play Success Indicators:**\n• Cat initiates play or shows excitement when toys appear\n• Healthy appetite after play sessions\n• Better sleep patterns and less nighttime activity\n• Maintained healthy weight and muscle tone\n• Reduced destructive or attention-seeking behaviors"
    ],
    'grooming': [
        "🧼 Proper grooming maintains cat health, comfort, and strengthens your bond:\n\n✂️ **Essential Grooming Tasks:**\n• **Brushing:** Daily for long-haired, 2-3 times weekly for short-haired\n• **Nail trimming:** Every 2-3 weeks for indoor cats\n• **Dental care:** Daily brushing ideal, minimum 3 times weekly\n• **Ear cleaning:** Weekly inspection, clean if dirty or waxy\n• **Eye cleaning:** Remove discharge with damp cloth as needed\n\n🪮 **Brushing Techniques:**\n• **Start slowly:** Short sessions, gradually increase duration\n• **Right tools:** Slicker brush for daily use, undercoat rake for shedding\n• **Direction:** Brush in direction of hair growth\n• **Problem areas:** Pay attention to chest, belly, behind legs\n• **Reward system:** Treats and praise make grooming positive\n\n💅 **Nail Trimming Guide:**\n• **Frequency:** Every 2-3 weeks, or when tips become sharp\n• **Tools:** Cat-specific nail clippers, never use human clippers\n• **Technique:** Gently press paw pad to extend claw, trim white tip only\n• **Safety:** Avoid pink 'quick' - causes pain and bleeding\n• **Gradual training:** Start by handling paws, reward with treats\n\n🦷 **Dental Care Importance:**\n• **Disease prevention:** 80% of cats have dental disease by age 3\n• **Daily brushing:** Use cat-specific toothpaste (never human toothpaste)\n• **Dental treats:** Supplement brushing with dental chews\n• **Professional cleaning:** Annual veterinary dental cleanings\n• **Warning signs:** Bad breath, yellow tartar, red gums, difficulty eating",
        "🐱 Comprehensive grooming for health, comfort, and bonding:\n\n🎯 **Coat Type-Specific Care:**\n\n**Short-Haired Cats:**\n• **Brushing:** 2-3 times weekly with rubber brush or fine-toothed comb\n• **Shedding season:** Daily brushing during spring and fall\n• **Benefits:** Reduces hairballs, distributes natural oils\n• **Tools:** Slicker brush, rubber grooming glove, fine comb\n\n**Long-Haired Cats:**\n• **Daily brushing:** Essential to prevent matting\n• **Sectional approach:** Work in small sections, be patient\n• **Mat prevention:** Pay special attention to chest, belly, legs\n• **Professional help:** Consider groomer for severe matting\n• **Tools:** Pin brush, wide-toothed comb, dematting tool\n\n**Special Considerations:**\n• **Senior cats:** May need help grooming hard-to-reach areas\n• **Overweight cats:** Cannot reach all areas, need assistance\n• **Medical conditions:** Arthritis may make self-grooming difficult\n• **Stress grooming:** Over-grooming may indicate anxiety or medical issues\n\n🛁 **Bathing Guidelines:**\n• **Rarely needed:** Most cats maintain cleanliness through self-grooming\n• **When necessary:** Skin conditions, flea treatments, extreme soiling\n• **Preparation:** Trim nails first, use lukewarm water, cat-specific shampoo\n• **Technique:** Support cat securely, work quickly but gently\n• **Drying:** Towel dry thoroughly, avoid blow dryers (too stressful)\n\n🏥 **Health Monitoring During Grooming:**\n• **Skin inspection:** Check for lumps, bumps, cuts, or irritation\n• **Parasite detection:** Look for fleas, ticks, or unusual scratching\n• **Ear health:** Note odor, discharge, or excessive wax\n• **Eye condition:** Clear, bright eyes with no discharge\n• **Overall condition:** Weight changes, muscle tone, mobility",
        "✨ Advanced grooming techniques and problem-solving for optimal cat care:\n\n🎯 **Grooming Challenges and Solutions:**\n\n**Mat Removal:**\n• **Prevention:** Daily brushing, especially during shedding season\n• **Early intervention:** Work out small mats with fingers and comb\n• **Severe matting:** Use dematting tools or seek professional help\n• **Never cut:** Avoid scissors near skin - easy to accidentally cut cat\n• **Professional grooming:** Sometimes full shave-down is necessary\n\n**Resistant Cats:**\n• **Gradual desensitization:** Start with short, positive sessions\n• **Treat association:** Pair grooming with high-value treats\n• **Timing:** Groom when cat is relaxed, not energetic\n• **Break it down:** Focus on one area per session initially\n• **Professional help:** Some cats need sedation for grooming\n\n**Senior Cat Grooming:**\n• **Gentle approach:** Arthritis may make positioning uncomfortable\n• **Shorter sessions:** Older cats tire more easily\n• **Focus areas:** Help with hard-to-reach spots (back, rear end)\n• **Health monitoring:** More frequent checks for lumps, skin changes\n• **Comfort first:** Use soft brushes, avoid pulling or tugging\n\n🧴 **Grooming Product Selection:**\n• **Brushes:** Quality tools last longer and work better\n• **Shampoos:** Cat-specific, pH-balanced formulations only\n• **Nail clippers:** Sharp, cat-sized clippers for clean cuts\n• **Dental products:** Enzymatic toothpaste, finger brushes\n• **Ear cleaners:** Veterinary-approved solutions only\n\n📅 **Grooming Schedule Template:**\n• **Daily:** Quick brush (long-haired), visual health check\n• **Weekly:** Thorough brushing, nail check, ear inspection\n• **Bi-weekly:** Nail trimming (if needed), dental care\n• **Monthly:** Complete grooming session, weight check\n• **Seasonally:** Professional grooming consultation if needed\n\n🏆 **Benefits of Regular Grooming:**\n• **Health monitoring:** Early detection of skin, ear, or dental issues\n• **Bonding time:** Positive interaction strengthens relationship\n• **Stress reduction:** Many cats find gentle grooming relaxing\n• **Cleanliness:** Reduces shedding, hairballs, and odors\n• **Comfort:** Prevents matting, overgrown nails, dental pain"
    ],
    'non_cat': [
        "🐱 I'm specialized in cat care only! I can help with feline health, behavior, diet, grooming, and general cat care questions. Please ask me about your cat's specific needs, and I'll provide detailed, helpful guidance.",
        "😺 I focus exclusively on cats! Please ask me about cat-related topics like health, emotions, behavior, nutrition, or care tips. I'm here to help with any feline concerns you might have.",
        "🐾 My expertise is all about cats! Feel free to ask about feline nutrition, behavior, health issues, grooming, litter box problems, or any other cat care concerns. I'm here to help you provide the best care for your feline friend."
    ]
}

def get_ai_response(question, cat_context=None):
    """Generate AI response based on question and cat context - CAT TOPICS ONLY"""
    question_lower = question.lower()
    
    # Check if question is cat-related
    cat_keywords = [
        'cat', 'kitten', 'feline', 'meow', 'purr', 'paw', 'whiskers', 'tail', 'fur',
        'litter', 'scratching', 'climbing', 'hunting', 'sleeping', 'grooming',
        'veterinarian', 'vet', 'pet', 'animal'
    ]
    
    # If question doesn't contain cat-related keywords, redirect to cat topics
    if not any(keyword in question_lower for keyword in cat_keywords):
        return random.choice(CAT_RESPONSES['non_cat'])
    
    # Determine response category based on cat-related content
    # Priority order: emotions first, then specific topics, then general
    if any(word in question_lower for word in ['sad', 'depressed', 'down', 'unhappy', 'hiding', 'withdrawn', 'lethargic']):
        category = 'emotion_sad'
    elif any(word in question_lower for word in ['angry', 'mad', 'aggressive', 'hostile', 'hissing', 'attacking', 'biting']):
        category = 'emotion_angry'
    elif any(word in question_lower for word in ['scared', 'afraid', 'fearful', 'hiding', 'trembling', 'cowering']):
        category = 'emotion_scared'
    elif any(word in question_lower for word in ['happy', 'joy', 'content', 'playful', 'purring', 'cheerful']):
        category = 'emotion_happy'
    elif any(word in question_lower for word in ['health', 'sick', 'ill', 'medical', 'illness', 'disease', 'symptoms', 'pain']):
        category = 'health'
    elif any(word in question_lower for word in ['food', 'diet', 'eating', 'nutrition', 'feed', 'hungry', 'appetite']):
        category = 'diet'
    elif any(word in question_lower for word in ['litter', 'box', 'toilet', 'bathroom', 'pee', 'poop', 'urinate', 'defecate']):
        category = 'litter'
    elif any(word in question_lower for word in ['play', 'toy', 'game', 'exercise', 'active', 'energy']):
        category = 'play'
    elif any(word in question_lower for word in ['groom', 'brush', 'clean', 'bath', 'nail', 'claw', 'fur', 'shedding']):
        category = 'grooming'
    elif any(word in question_lower for word in ['behavior', 'acting', 'doing', 'why', 'meow', 'purr', 'scratch']):
        category = 'behavior'
    elif any(word in question_lower for word in ['hello', 'hi', 'hey', 'start', 'help', 'greeting']):
        category = 'greeting'
    else:
        category = 'behavior'  # Default to behavior for cat-related questions
    
    base_response = random.choice(CAT_RESPONSES[category])
    
    # Add personalized context if available
    if cat_context:
        cat_name = cat_context.get('cat_name', 'your cat')
        recent_emotions = cat_context.get('recent_emotions', [])
        
        if recent_emotions:
            emotion_context = f"\n\n🐾 Based on {cat_name}'s recent AI emotion analysis showing {', '.join(recent_emotions[:3])}, "
            
            if 'Happy' in recent_emotions or 'Resting' in recent_emotions:
                emotion_context += f"{cat_name} seems to be doing wonderfully! Keep up the excellent care."
            elif any(emotion in recent_emotions for emotion in ['Sad', 'Angry', 'Scared', 'Paining']):
                emotion_context += f"I recommend monitoring {cat_name} closely and considering what might be causing stress or discomfort."
            elif 'Fighting' in recent_emotions or 'Warning' in recent_emotions:
                emotion_context += f"{cat_name} may be feeling territorial or defensive. Ensure they have safe spaces."
            else:
                emotion_context += f"{cat_name} appears to be in a normal emotional state."
            
            base_response += emotion_context
    
    return base_response

@login_required
def ai_chat(request):
    """AI chat interface"""
    user_cats = CatProfile.objects.filter(owner=request.user)
    recent_conversations = AIConversation.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'user_cats': user_cats,
        'recent_conversations': recent_conversations,
    }
    return render(request, 'ai_assistant/chat.html', context)

@login_required
@csrf_exempt
def ask_question(request):
    """Handle AI question via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question', '').strip()
            cat_id = data.get('cat_id')
            
            if not question:
                return JsonResponse({'error': 'Question is required'}, status=400)
            
            # Get cat context if specified
            cat_context = None
            cat = None
            
            if cat_id:
                try:
                    cat = CatProfile.objects.get(id=cat_id, owner=request.user)
                    
                    # Get recent emotions for context
                    recent_predictions = EmotionPrediction.objects.filter(
                        cat=cat
                    ).order_by('-created_at')[:5]
                    
                    recent_emotions = [pred.predicted_emotion for pred in recent_predictions]
                    
                    cat_context = {
                        'cat_name': cat.name,
                        'recent_emotions': recent_emotions,
                        'age': cat.age,
                        'breed': cat.breed
                    }
                except CatProfile.DoesNotExist:
                    pass
            
            # Generate AI response
            answer = get_ai_response(question, cat_context)
            
            # Save conversation
            conversation = AIConversation.objects.create(
                user=request.user,
                cat=cat,
                question=question,
                answer=answer,
                context_used=cat_context
            )
            
            return JsonResponse({
                'success': True,
                'answer': answer,
                'conversation_id': conversation.id,
                'timestamp': conversation.created_at.isoformat()
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def conversation_history(request):
    """View conversation history"""
    conversations = AIConversation.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(conversations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'conversations': page_obj,
    }
    return render(request, 'ai_assistant/history.html', context)

@login_required
@csrf_exempt
def clear_history(request):
    """Clear conversation history"""
    if request.method == 'POST':
        try:
            # Delete all conversations for the user
            deleted_count = AIConversation.objects.filter(user=request.user).delete()[0]
            
            return JsonResponse({
                'success': True,
                'message': f'Cleared {deleted_count} conversations',
                'deleted_count': deleted_count
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
@csrf_exempt
def delete_conversation(request):
    """Delete specific conversation"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            conversation_id = data.get('conversation_id')
            
            if not conversation_id:
                return JsonResponse({'error': 'Conversation ID is required'}, status=400)
            
            conversation = AIConversation.objects.get(
                id=conversation_id, 
                user=request.user
            )
            conversation.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Conversation deleted successfully'
            })
            
        except AIConversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
