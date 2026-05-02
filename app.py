from flask import Flask, render_template, request, jsonify
from core import MemoryManager
import logging

app = Flask(__name__)
# Keep logs quiet for cleaner output unless error
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

# Initialize with some default blocks
# To show internal fragmentation easily, wait, we can just start with 1000 split dynamically.
# Let's start with a dynamic 1000 size block.
memory_manager = MemoryManager(block_sizes=[1000])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/allocate', methods=['POST'])
def allocate():
    data = request.json
    process_id = data.get('process_id')
    size = int(data.get('size', 0))
    algorithm = data.get('algorithm', 'first_fit')
    
    if not process_id or size <= 0:
        return jsonify({"error": "Invalid process ID or size"}), 400
        
    # Check if process_id already exists
    for b in memory_manager.blocks:
        if b.allocated and b.process_id == process_id:
            return jsonify({"error": "Process ID already exists"}), 400
            
    success = False
    if algorithm == 'first_fit':
        success = memory_manager.first_fit(process_id, size)
    elif algorithm == 'best_fit':
        success = memory_manager.best_fit(process_id, size)
    elif algorithm == 'worst_fit':
        success = memory_manager.worst_fit(process_id, size)
    else:
        return jsonify({"error": "Invalid algorithm"}), 400
        
    if success:
        return jsonify({"message": "Allocated successfully", "status": memory_manager.get_status()})
    else:
        return jsonify({"error": "Allocation failed: Not enough contiguous memory"}), 400

@app.route('/deallocate', methods=['POST'])
def deallocate():
    data = request.json
    process_id = data.get('process_id')
    
    if not process_id:
        return jsonify({"error": "Invalid process ID"}), 400
        
    found = False
    for b in memory_manager.blocks:
        if b.allocated and b.process_id == process_id:
            found = True
            break
            
    if not found:
        return jsonify({"error": f"Process ID {process_id} not found"}), 404
        
    memory_manager.deallocate(process_id)
    return jsonify({"message": "Deallocated successfully", "status": memory_manager.get_status()})

@app.route('/reset', methods=['POST'])
def reset():
    data = request.json
    try:
        # User provides sizes as comma-separated
        blocks_input = data.get('block_sizes', '1000')
        split_blocks = data.get('split_blocks', True)
        sizes = [int(s.strip()) for s in str(blocks_input).split(',') if s.strip()]
        if not sizes:
            sizes = [1000]
        memory_manager.reset(sizes, split_blocks)
        return jsonify({"message": "Memory reset successfully", "status": memory_manager.get_status()})
    except Exception as e:
        return jsonify({"error": f"Invalid configuration: {str(e)}"}), 400

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify(memory_manager.get_status())

if __name__ == '__main__':
    app.run(debug=True, port=5000)
