from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from jsonclass import QuizResponse  # Import the WRAPPER, not the single question

parser = JsonOutputParser(pydantic_object=QuizResponse)

template = """
You are an expert university professor writing a rigorous, advanced exam paper.
Write EXACTLY {num_questions} Multiple Choice Question(s) about {topic}. 
The questions must be challenging, testing deep comprehension and 
applied knowledge rather than mere rote memorization. Distribute the question 
types according to the following strict hierarchy:
**PRIORITY 1: Scenario based questions** 
Provide a realistic situation, architecture dilemma, or code snippet. Ask 
the student to diagnose the issue, predict the outcome, or choose the optimal 
solution. Do not ask purely theoretical questions here.
**PRIORITY 2: Command and syntax based questions** 
Provide a specific operational scenario and ask which exact command or script 
should be executed to achieve the goal. The incorrect options (distractors) MUST 
be highly plausible, using realistic flags or syntax errors that commonly confuse 
engineers.
**PRIORITY 3: Theoretical Definition (Maximum 1 question per batch)** 
Focus on the core definition, underlying mechanism, or primary usage of a concept.
Syllabus Text:
{context}

{format_instructions}

CRITICAL RULES:
1. SOURCE TRUTH: ALL questions MUST test knowledge found explicitly in the Syllabus Text provided.
2. STANDALONE FORMAT: ALL questions MUST read naturally as standalone exam questions. NEVER reference 
    the "syllabus," "text," "context," or "provided information." in the question or the options.
3. BAD QUESTION: "Based on the provided context, what does a Kubernetes Deployment do?"
4. GOOD QUESTION: "Which Kubernetes resource ensures that a specified number of pod replicas are 
    actively running and replaces them if a node fails?"
5. BREVITY: Be concise. Avoid wordy preambles or repeating facts from the syllabus within the question 
    text unless necessary for a scenario.
6. PLAUSIBLE DISTRACTORS: All incorrect options across all question types must be realistic and 
    common misconceptions. 
7. THE EXPLANATION: The explanation field MUST thoroughly explain why the correct answer is right 
    AND explicitly debunk why each of the other options is incorrect.
8. ESCAPE HATCH: If the Syllabus Text lacks sufficient information about {topic} to generate the 
    requested number of questions, output "NO_DATA" for the question and correct_answer fields for 
    any unfillable quota.
"""

prompt = PromptTemplate(
    template=template,
    input_variables=["topic", "context"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)