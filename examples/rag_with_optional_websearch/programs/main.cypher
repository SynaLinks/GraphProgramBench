// @desc: The main program
CREATE
(start:Control {name:"Start"}),
(end:Control {name:"End"}),
(is_websearch_needed:Decision {
    name:"Check if searching for information online is needed to answer the objectve's question",
    question:"Is searching online needed to answer the objective's question?"
}),
(websearch:Action {
    name: "Perform a duckduckgo search",
    tool: "DuckDuckGoSearch",
    prompt: "Infer the search query to answer the given question"
}),
(answer:Action {
    name:"Answer the objective's question",
    tool:"Predict",
    prompt:"You are an helpfull assistant, answer the given question"
}),
(start)-[:NEXT]->(is_websearch_needed),
(is_websearch_needed)-[:YES]->(websearch),
(is_websearch_needed)-[:MAYBE]->(websearch),
(is_websearch_needed)-[:UNKNOWN]->(websearch),
(is_websearch_needed)-[:NO]->(answer),
(websearch)-[:NEXT]->(answer),
(answer)-[:NEXT]->(end)