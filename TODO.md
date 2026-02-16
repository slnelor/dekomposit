# Agentic behaviour
1. The agent is overdoing his work sometimes, for example it may use the tool when it isn't needed.
Like "User: Ako sa mas?; Agent: **used translation tool** How are you?" <- I just asked how is it going.

2. The agent does not keep the words right sometimes. For example:
"User: Help me learning 'vobec'; Agent: ... vobec ... <- correct 'vôbec' 

3. The agent is not agentic.
   a) Add more tools
   b) Customize the agent more
     I) More creativity - DONE
     II) Have own opinions - DONE
     III) Have own style - DONE
     IV) Analyze his mistakes - PENDING
     V) Add templates for practice quizes, etc... - PENDING
   c) Write a dataset with propper agentic behaviour

4. It sucks - feels like talking to gpt-4o (actually it's gemini-flash-latest)

5. Fine-tune own model
   a) create & aggregate a new dataset
   b) choose the model
   c) fine-tune this
   d) deploy

---

# Refactoring (Completed)

## Tool System
- ToolRegistry with auto-discovery - DONE
- Unified tag+template system (FormatRegistry) - DONE

## Code Organization
- Types moved to types.py - DONE
- Language detection now via LLM (not local) - DONE
- Base prompts renamed to base_prompts/ - DONE
- Removed unused methods from agent.py - DONE

## Architecture
- docs/ARCHITECTURE.md created - DONE
