// @desc: The main program
CREATE
(start:Control {name:"Start"}),
(end:Control {name:"End"}),
(document_search:Action {
    name: "Search to documents to answer the objective's question",
    tool: "DocumentSearch",
    prompt: "Use the objective's question to infer the search query"
}),
(is_answer_known:Decision {
    name:"Check if the answer to the objective's question is in the above search",
    question: "Is the answer in the context?"
}),
(websearch:Action {
    name: "Perform a duckduckgo search",
    tool: "DuckDuckGoSearch",
    prompt: "Use the objective's question to infer the search query"
}),
(answer_web:Action {
    name: "Answer the objective's question based on the web search",
    tool: "Predict",
    prompt: "Use the above web search to infer the answer"
}),
(answer:Action {
    name: "Answer the objective's question based on the document search",
    tool: "Predict",
    prompt: "Use the above document search to infer the answer"
}),
(save_answer:Action {
    name: "Save the answer to the objective's question in a .txt file",
    tool: "WriteFile",
    prompt: "Use the final answer to the objective's question to infer the content of the file,
Use the objective's question to infer its snake case filename
The content should be ONE paragraph only containing the answer.
Please always ensure to correctly infer the content of the file, don't be lazy."
}),
(start)-[:NEXT]->(document_search),
(document_search)-[:NEXT]->(is_answer_known),
(is_answer_known)-[:YES]->(answer),
(is_answer_known)-[:NO]->(websearch),
(websearch)-[:NEXT]->(answer_web),
(answer_web)-[:NEXT]->(save_answer),
(save_answer)-[:NEXT]->(end),
(answer)-[:NEXT]->(end)