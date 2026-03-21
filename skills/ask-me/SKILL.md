---
name: ask-me
description: Use when the user says "ask me", "you ask questions", or when creating plans/designs to ensure all design details are clarified. Also use after file modifications to understand the intent of changes. CRITICAL: Use when YOU (the AI) are confused, uncertain about how to proceed, or when the user's instructions are ambiguous or unclear — DO NOT guess, invoke this skill instead.
---

# Ask Me Skill

A skill for systematic questioning to ensure alignment before proceeding with work.

## When to Use This Skill

Trigger this skill when:
1. User explicitly says "ask me", "you ask me questions", or similar phrases
2. User is creating a plan or design solution and design details need clarification
3. User has modified a file and the intent of changes should be understood
4. Any situation where uncertainty exists about user intent
5. **YOU (the AI) are confused**: You are unsure how to execute the task, don't understand the user's goal, or lack critical information — **do NOT guess, invoke this skill immediately**
6. **User's instructions are unclear**: The request is ambiguous, missing key details, or can be interpreted in multiple significantly different ways

## Core Principles

1. **Question Iteratively**: Ask questions until alignment is reached
2. **First Round Questions**: Ask between 3-20 questions in the first round (when no prior questioning context exists)
3. **Continuous Questioning**: Continue questioning in subsequent rounds until intent is fully understood
4. **Hybrid Alignment Detection**: Infer alignment when the user gives clear confirmation (yes, correct, that's right), but explicitly ask "Are we aligned?" when uncertain

## Questioning Strategy

### For Plans and Designs

When the user is creating a plan or design:
- Explore the full branch of the design tree
- Ask about specific implementation details
- Clarify edge cases and constraints
- Understand success criteria

**Example questions:**
- What are the key constraints for this solution?
- Which parts of the design are flexible vs. fixed?
- What does success look like for this implementation?
- Are there edge cases we should consider?

### For File Modifications

When reviewing file changes:
- Focus on significant changes (ignore whitespace and minor style edits)
- Ask about the intent behind each meaningful modification
- Point out contradictions immediately if detected

**Example questions:**
- What was the reason for modifying this function?
- Why was this particular approach chosen?
- I see you changed X here, but earlier you mentioned Y - can you clarify?

### When User Says "Ask Me"

- Start with 3-20 relevant questions based on context
- Cover the main aspects of what needs to be understood
- Continue with follow-up questions until alignment

### When AI is Confused or Instructions are Unclear

**This is a mandatory trigger — do NOT guess and proceed.** When you encounter any of the following, invoke this skill immediately:

- You are unsure what the user wants you to do
- The request has multiple plausible interpretations that lead to very different outcomes
- Critical information is missing (scope, target file, expected behavior, constraints)
- You find yourself about to make an assumption just to move forward

**How to ask:**
1. State concisely what you are confused about: "I'm unclear about X"
2. If there are 2-3 distinct interpretations, list them explicitly and ask the user to choose
3. If information is simply missing, ask the specific question needed

**Example questions:**
- "I'm not sure which files you want me to modify — did you mean A or B?"
- "This could mean X or Y — which did you intend?"
- "I'm missing [specific info] before I can proceed. Can you clarify?"

**Anti-pattern to avoid:** Picking one interpretation, executing it, then asking "Is this what you meant?" — this wastes time and may cause unwanted changes.

## Handling User Responses

### Confirmation Signals (inferred alignment)
- "Yes", "correct", "that's right", "exactly"
- "Agreed", "sounds good", "that works"
- Nod emojis or clear affirmative statements

### Uncertainty Signals (explicit alignment check needed)
- "I think so", "maybe", "not sure"
- "Hmm", "let me think", vague responses
- Partial or qualified agreement ("yes, but...")
- Any response that leaves ambiguity

### Contradictions
- **Point out immediately**: If you detect a contradiction in the user's responses, flag it right away
- Example: "Earlier you mentioned X, but now you're saying Y. Can you help me understand how these fit together?"

## When to Stop Questioning

Stop when:
1. User gives clear, consistent confirmation signals
2. No significant ambiguities remain
3. All key design branches have been explored
4. You receive an explicit "we're aligned" or similar

## Important Notes

- **不要猜测再执行**：如果你不确定用户的意图，永远优先调用此 skill 提问，而不是假设一种解读然后执行。错误的执行比多问一个问题代价高得多。
- This skill does NOT remember preferences across sessions - each conversation starts fresh
- Be respectful of the user's time - ask focused, relevant questions
- If the user seems frustrated or impatient, briefly explain why the question matters and move on
- Adapt question count based on complexity - simpler tasks need fewer questions
