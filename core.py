class MemoryBlock:
    def __init__(self, size, process_id=None, allocated=False):
        self.size = size
        self.process_id = process_id
        self.allocated = allocated
        self.process_size = size if allocated else 0

class MemoryManager:
    def __init__(self, block_sizes):
        # Initialize memory with fixed or given blocks.
        # If user provides total size for purely dynamic, it will be a single large block
        # For our visualization, we treat the initial state as the available blocks
        self.blocks = [MemoryBlock(size=int(s)) for s in block_sizes]
        self.is_dynamic = len(self.blocks) == 1  # If only 1 block provided initially, we assume dynamic splitting is allowed. Actually let's configure this explicitly.
        
        # We will add an option to dynamically split blocks if desired,
        # but the prompt says 'Represent memory as blocks (variable size)'
        # To calculate Internal Fragmentation, we can allocate a block without splitting it.
        # Let's allow splitting if requested, but for now we follow:
        # Standard dynamic memory: We do NOT split by default to show internal fragmentation, 
        # OR we split. Let's provide standard Best/First/Worst fit over the current blocks.
        self.split_blocks = True

    def reset(self, block_sizes, split_blocks=True):
        self.blocks = [MemoryBlock(size=int(s)) for s in block_sizes]
        self.split_blocks = split_blocks

    def first_fit(self, process_id, size):
        for i, block in enumerate(self.blocks):
            if not block.allocated and block.size >= size:
                return self._allocate_at(i, process_id, size)
        return False

    def best_fit(self, process_id, size):
        best_idx = -1
        best_diff = float('inf')
        for i, block in enumerate(self.blocks):
            if not block.allocated and block.size >= size:
                diff = block.size - size
                if diff < best_diff:
                    best_diff = diff
                    best_idx = i
        
        if best_idx != -1:
            return self._allocate_at(best_idx, process_id, size)
        return False

    def worst_fit(self, process_id, size):
        worst_idx = -1
        worst_diff = -1
        for i, block in enumerate(self.blocks):
            if not block.allocated and block.size >= size:
                diff = block.size - size
                if diff > worst_diff:
                    worst_diff = diff
                    worst_idx = i
        
        if worst_idx != -1:
            return self._allocate_at(worst_idx, process_id, size)
        return False

    def _allocate_at(self, idx, process_id, size):
        block = self.blocks[idx]
        if self.split_blocks and block.size > size:
            # Split the block
            remaining_size = block.size - size
            
            # The allocated part
            block.size = size
            block.allocated = True
            block.process_id = process_id
            block.process_size = size
            
            # The free part
            new_block = MemoryBlock(size=remaining_size)
            self.blocks.insert(idx + 1, new_block)
        else:
            # Allocate whole block (leads to internal fragmentation)
            block.allocated = True
            block.process_id = process_id
            block.process_size = size
        return True

    def deallocate(self, process_id):
        # Find and free the process
        for block in self.blocks:
            if block.allocated and block.process_id == process_id:
                block.allocated = False
                block.process_id = None
                block.process_size = 0
        self._merge_free_blocks()
        return True

    def _merge_free_blocks(self):
        # Merges adjacent free blocks if dynamic splitting is on
        # Even if not, merging contiguous free space might make sense, 
        # but let's do it if we are using dynamic blocks
        if not self.split_blocks:
            return
            
        i = 0
        while i < len(self.blocks) - 1:
            if not self.blocks[i].allocated and not self.blocks[i+1].allocated:
                self.blocks[i].size += self.blocks[i+1].size
                del self.blocks[i+1]
            else:
                i += 1

    def get_status(self):
        total_memory = sum(b.size for b in self.blocks)
        allocated_memory = sum(b.size for b in self.blocks if b.allocated)
        
        # Internal fragmentation: sum of (block_size - process_size) for allocated blocks!
        internal_frag = sum(b.size - b.process_size for b in self.blocks if b.allocated)
        
        # External fragmentation: total free space
        # Usually it is considered the sum of free sizes when an allocation fails, 
        # but we can report the sum of all free blocks.
        external_frag = sum(b.size for b in self.blocks if not b.allocated)
        
        utilization = 0
        if total_memory > 0:
            utilization = (allocated_memory / total_memory) * 100
        
        return {
            "blocks": [{"size": b.size, "allocated": b.allocated, "process_id": b.process_id, "process_size": b.process_size} for b in self.blocks],
            "internal_fragmentation": internal_frag,
            "external_fragmentation": external_frag,
            "utilization": round(utilization, 2),
            "total_memory": total_memory
        }
