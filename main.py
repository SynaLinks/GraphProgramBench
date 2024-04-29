import dspy
import sys
import argparse
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
import os
from hybridagi import GraphProgramInterpreter
from hybridagi import SentenceTransformerEmbeddings
from hybridagi import ProgramMemory, TraceMemory, FileSystem, AgentState
from hybridagi.tools import (
    DuckDuckGoSearchTool,
    ProgramSearchTool,
    DocumentSearchTool,
    CallProgramTool,
    PredictTool,
    InternalShellTool,
    WriteFileTool,
    AppendFileTool,
    ReadFileTool,
    SpeakTool,
    AskUserTool,
    UpdateObjectiveTool,
    UploadTool,
    ClearTraceTool,
    PastActionSearchTool,
    #PlannifyProgramTool,
    #ChainOfThoughtTool,
    #ProgramOfThoughtTool,
    ReadProgramTool,
    RevertTraceTool,
    WriteProgramTool,
)
from pydantic import BaseModel
from dspy.teleprompt import BootstrapFewShotWithRandomSearch


class AssessAnswer(dspy.Signature):
    """Assess the success of the trace according to the objective"""
    assessed_answer = dspy.InputField(desc="The answer to assess")
    assessed_question = dspy.InputField(desc="The question to be assessed")
    critique = dspy.OutputField(desc="The critique of the answer")

class Score(BaseModel):
    score: float

class CritiqueToScoreSignature(dspy.Signature):
    """Convert a critique into a score between 0.0 and 1.0"""
    critique = dspy.InputField(desc="The critique to convert into a score")
    score: Score = dspy.OutputField(desc="A score between 0.0 and 1.0")

def case_setup(example_index, embeddings):

    #print("Initializing the program memory...")
    program_memory = ProgramMemory(
        index_name = example_index,
        embeddings = embeddings,
        wipe_on_start = True,
    )

    #print("Initializing the trace memory...")
    trace_memory = TraceMemory(
        index_name = example_index,
        embeddings = embeddings,
        wipe_on_start = True,
    )

    #print("Initializing the internal filesystem...")
    filesystem = FileSystem(
        index_name = example_index,
        embeddings = embeddings,
    )
    
    agent_state = AgentState()

    tools = [
        DuckDuckGoSearchTool(),
        PredictTool(),
        ProgramSearchTool(
            program_memory = program_memory,
            embeddings = embeddings,
        ),
        DocumentSearchTool(
            filesystem = filesystem,
            embeddings = embeddings,
        ),
        CallProgramTool(
            program_memory = program_memory,
            agent_state = agent_state,
        ),
        InternalShellTool(
            filesystem = filesystem,
            agent_state = agent_state,
        ),
        WriteFileTool(
            filesystem = filesystem,
            agent_state = agent_state,
        ),
        AppendFileTool(
            filesystem = filesystem,
            agent_state = agent_state,
        ),
        ReadFileTool(
            filesystem = filesystem,
            agent_state = agent_state,
        ),
        UploadTool(
            filesystem = filesystem,
            agent_state = agent_state,
        ),
        SpeakTool(
            agent_state = agent_state,
        ),
        AskUserTool(
            agent_state = agent_state,
        ),
        UpdateObjectiveTool(
            agent_state=agent_state
        ),
        UploadTool(
            filesystem=filesystem,
            agent_state=agent_state
        ),
        ClearTraceTool(
            agent_state=agent_state
        ),
        PastActionSearchTool(
            trace_memory=trace_memory,
            embeddings=embeddings
        ),
        InternalShellTool(
            filesystem=filesystem,
            agent_state=agent_state
        ),
        ReadProgramTool(
            program_memory=program_memory
        ),
        RevertTraceTool(
            agent_state=agent_state
        ),
        WriteProgramTool(
            program_memory=program_memory
        )
    ]

    program_memory.add_folders(["examples/primitives", "examples/"+example_index+"/programs"])

    interpreter = GraphProgramInterpreter(
                program_memory = program_memory,
                trace_memory = trace_memory,
                agent_state = agent_state,
                tools = tools,
            )

    return program_memory, trace_memory, filesystem, agent_state, tools, interpreter

def main() -> int:
    parser = argparse.ArgumentParser(description="This is a benchmarking program designed to run evaluations of LLMs using HybridAGI to address complex tasks.\n"
                                     +"You can run evaluations on the examples or load some from a json file.")
    parser.add_argument("LLM_list", nargs='+', help="Required argument. List of LLMs on which to perform evaluations and comparison.")
    parser.add_argument("--json", metavar="FILE", help="Path of examples json file to read from.")
    #TODO add verbose mode?
    args = parser.parse_args()

    print("Required argument:", args.LLM_list)
    if args.json:
        print("Optional argument:", args.json)

    embeddings = SentenceTransformerEmbeddings(dim=384, model_name_or_path="sentence-transformers/all-MiniLM-L6-v2")

    examples = [example for example in os.listdir("examples") if os.path.isdir(os.path.join("examples", example)) and example != 'primitives']

    config = dict(max_bootstrapped_demos=4, max_labeled_demos=4)

    models_scores = {}

    for model_name in tqdm(args.LLM_list):
        student_llm = dspy.OllamaLocal(model=model_name, max_tokens=1024, stop=["\n\n\n"])
        teacher_llm = dspy.OllamaLocal(model=model_name, max_tokens=1024, stop=["\n\n\n"])

        dspy.settings.configure(lm=student_llm)

        def program_success(example, pred, trace=None):
                question = example.objective
                with dspy.context(lm=teacher_llm):
                    prediction = dspy.ChainOfThought(AssessAnswer)(
                        assessed_answer = pred.final_answer,
                        assessed_question = question,
                    )
                    result = dspy.TypedPredictor(CritiqueToScoreSignature)(critique=prediction.critique)
                return result.score.score
        
        """ optimizer = BootstrapFewShotWithRandomSearch(
            num_threads = 1,
            teacher_settings=dict({'lm': teacher_llm}),
            metric = program_success,
            **config,
        ) """

        scores = []

        for example_index in examples:
            program_memory, trace_memory, filesystem, agent_state, tools, interpreter = case_setup(example_index, embeddings)
            with open("examples/"+example_index+"/objectives.json", 'r') as objectives_f:
                objectives = json.load(objectives_f)
            dataset, testset = objectives["dataset"], objectives["testset"]

            """ compiled_interpreter = optimizer.compile(
                interpreter,
                trainset=[dspy.Example(objective).with_inputs("objective") for objective in dataset],
                valset=testset,
            ) """

            evaluate = dspy.evaluate.Evaluate(
                devset = [dspy.Example(objective).with_inputs("objective") for objective in testset],
                metric = program_success,
                num_threads = 1,
                display_progress = False,
                display_table = 0,
            )
            try:
                baseline_score = evaluate(interpreter)
            except Exception:
                baseline_score = 0.0
            
            scores.append(baseline_score)
        
        print(scores)
        print(f"{model_name} achieved average score of {np.mean(scores)}")

        models_scores[model_name] = scores

    results = pd.DataFrame(models_scores.values(), columns=examples, index=models_scores.keys())
    results["average"] = results.mean(axis=1)
    print(results)
        
    return 0

if __name__ == "__main__":
    sys.exit(main())