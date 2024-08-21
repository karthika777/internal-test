import asyncio
import gradio as gr
from nbclient import NotebookClient
from nbformat import read, v4 as nbf
import time

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

cache = {}
notebook_executed = False
executed_notebook = None  # To store the state of the executed notebook

def run_notebook(notebook_path, query_str):
    global notebook_executed, executed_notebook
    
    # If the notebook has been executed before and the query is in cache, return cached output
    if notebook_executed and query_str in cache:
        return cache[query_str]
    
    # Load the notebook
    with open(notebook_path) as f:
        notebook = read(f, as_version=4)
        
    query_str_cell = f"query_str = \"{query_str}\""
    
    # On the first run, execute the entire notebook
    if not notebook_executed:
        notebook.cells.insert(0, nbf.new_code_cell(query_str_cell))  # Insert query_str at the beginning
        
        client = NotebookClient(notebook)
        client.execute()
        
        executed_notebook = notebook  # Store the executed notebook state
        notebook_executed = True
    
    else:
        # Reuse the executed notebook, only execute the last three cells with updated query_str
        if executed_notebook:
            executed_notebook.cells[-3].source = query_str_cell + "\n" + executed_notebook.cells[-3].source.split('\n', 1)[1]
            notebook.cells[-3:] = executed_notebook.cells[-3:]  # Replace the last 3 cells
            
            client = NotebookClient(notebook)
            client.execute()
    
    # Collect the output
    output = ""
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            for out in cell.outputs:
                if out.output_type == 'stream':
                    output += out.text
                elif out.output_type == 'execute_result':
                    output += out.data['text/plain']

    # Cache the output for the query
    cache[query_str] = output

    return output

def chat_interface(query_str, history):
    # Make sure the query_str is passed to the notebook execution
    notebook_path = 'pqe.ipynb'
    output = run_notebook(notebook_path, query_str)
    words = output.split()
    ans = ""
    for token in words:
        ans = ans + " " + token
        time.sleep(0.1)
        yield ans

iface = gr.ChatInterface(
    fn=chat_interface,
    title="LogSeek - AI",
    theme="default"
)

if __name__ == "__main__":
    iface.launch(server_name="localhost", server_port=7890)