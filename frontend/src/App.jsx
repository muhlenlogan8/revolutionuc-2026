import { useState, useEffect } from "react";

const App = () => {
	const [tools, setTools] = useState([]);
	const [toolsChanged, setToolsChanged] = useState(false);

	useEffect(() => {
		fetch("http://127.0.0.1:8000/tools")
			.then((res) => res.json())
			.then((data) => setTools(data));
	}, [toolsChanged]);

	const addTool = async () => {
		await fetch("http://127.0.0.1:8000/tools?name=test&state=out", {
			method: "POST",
		});

		setToolsChanged((prev) => !prev);
	};

	return (
		<div className="p-8">
			<h1 className="text-3xl font-bold mb-6">Tools</h1>
			<div className="grid gap-4">
				{tools.map((tool) => (
					<div
						key={tool.id}
						className="flex mx-auto w-full justify-between border rounded-lg p-4 shadow-md"
					>
						<h2 className="font-semibold text-lg">{tool.name}</h2>
						<p className="font-semibold text-lg">{tool.state}</p>
						<p className="font-semibold text-lg">{tool.last_state_change}</p>
					</div>
				))}
			</div>
			<button
				onClick={addTool}
				className="mt-6 px-6 py-3 bg-green-500 hover:bg-green-600 text-white font-bold rounded-lg shadow-md transition-colors"
			>
				Add Tool
			</button>
		</div>
	);
};

export default App;
