"""
Example demonstrating the use of the Agent Discovery and Capabilities Registry.

This example shows how to:
1. Register agents with the discovery service
2. Register capabilities with the capabilities registry
3. Find agents by capability
4. Negotiate capabilities with agents
5. Validate data against capability schemas
"""

import asyncio
import json
from datetime import datetime

from src.orchestrator.agent_discovery import (
    get_agent_discovery_service,
    get_agent_capabilities_registry
)


async def main():
    """Run the example."""
    print("Agent Discovery and Capabilities Registry Example")
    print("=" * 50)
    
    # Get the agent discovery service and capabilities registry
    discovery_service = get_agent_discovery_service()
    capabilities_registry = get_agent_capabilities_registry()
    
    # Register some capabilities
    print("\n1. Registering capabilities...")
    
    # Register a simple capability
    await capabilities_registry.register_capability(
        name="text_processing",
        description="Process and analyze text",
        versions=["1.0.0", "1.1.0", "2.0.0"],
        metadata={
            "category": "nlp",
            "languages": ["en", "fr", "es"]
        }
    )
    
    # Register a capability with a schema
    await capabilities_registry.register_capability(
        name="image_generation",
        description="Generate images from text prompts",
        versions=["1.0.0"],
        schema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "width": {"type": "integer", "minimum": 64, "maximum": 1024},
                "height": {"type": "integer", "minimum": 64, "maximum": 1024},
                "style": {"type": "string", "enum": ["realistic", "cartoon", "abstract"]}
            },
            "required": ["prompt"]
        },
        metadata={
            "category": "image",
            "models": ["stable-diffusion", "dall-e"]
        }
    )
    
    # Register a capability for code generation
    await capabilities_registry.register_capability(
        name="code_generation",
        description="Generate code from natural language descriptions",
        versions=["1.0.0", "2.0.0"],
        schema={
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "language": {"type": "string"},
                "framework": {"type": "string"},
                "max_tokens": {"type": "integer", "minimum": 1}
            },
            "required": ["description", "language"]
        },
        metadata={
            "category": "code",
            "languages": ["python", "javascript", "java", "c++", "go"]
        }
    )
    
    # List all registered capabilities
    capabilities = await capabilities_registry.list_capabilities()
    print(f"Registered {len(capabilities)} capabilities:")
    for cap in capabilities:
        print(f"  - {cap['name']} ({', '.join(cap['versions'])}): {cap['description']}")
    
    # Register some agents
    print("\n2. Registering agents...")
    
    # Register a text processing agent
    await discovery_service.register_agent(
        agent_id="text-agent-1",
        name="Text Processing Agent",
        capabilities=[
            {"name": "text_processing", "version": "2.0.0"}
        ],
        status="idle",
        metadata={
            "provider": "OpenAI",
            "model": "gpt-4",
            "max_tokens": 8192
        }
    )
    
    # Register an image generation agent
    await discovery_service.register_agent(
        agent_id="image-agent-1",
        name="Image Generation Agent",
        capabilities=[
            {"name": "image_generation", "version": "1.0.0"}
        ],
        status="idle",
        metadata={
            "provider": "Stability AI",
            "model": "stable-diffusion-xl",
            "max_resolution": "1024x1024"
        }
    )
    
    # Register a multi-capability agent
    await discovery_service.register_agent(
        agent_id="multi-agent-1",
        name="Multi-Capability Agent",
        capabilities=[
            {"name": "text_processing", "version": "1.1.0"},
            {"name": "code_generation", "version": "2.0.0"}
        ],
        status="idle",
        metadata={
            "provider": "Anthropic",
            "model": "claude-3",
            "max_tokens": 100000
        }
    )
    
    # List all registered agents
    agents = await discovery_service.list_agents()
    print(f"Registered {len(agents)} agents:")
    for agent in agents:
        capabilities = [f"{cap['name']} v{cap['version']}" for cap in agent["capabilities"]]
        print(f"  - {agent['name']} ({agent['agent_id']}): {', '.join(capabilities)}")
    
    # Find agents by capability
    print("\n3. Finding agents by capability...")
    
    # Find agents with text processing capability
    text_agents = await discovery_service.find_agents_by_capability(
        capability="text_processing"
    )
    print(f"Found {len(text_agents)} agents with text_processing capability:")
    for agent in text_agents:
        print(f"  - {agent['name']} ({agent['agent_id']})")
    
    # Find agents with code generation capability
    code_agents = await discovery_service.find_agents_by_capability(
        capability="code_generation",
        version="2.0.0"
    )
    print(f"Found {len(code_agents)} agents with code_generation v2.0.0 capability:")
    for agent in code_agents:
        print(f"  - {agent['name']} ({agent['agent_id']})")
    
    # Find agents with multiple capabilities
    multi_agents = await discovery_service.find_agents_by_capabilities(
        capabilities=[
            {"name": "text_processing"},
            {"name": "code_generation"}
        ],
        match_all=True
    )
    print(f"Found {len(multi_agents)} agents with both text_processing and code_generation capabilities:")
    for agent in multi_agents:
        print(f"  - {agent['name']} ({agent['agent_id']})")
    
    # Negotiate capabilities with an agent
    print("\n4. Negotiating capabilities with agents...")
    
    # Negotiate with multi-agent-1
    negotiation_result = await discovery_service.negotiate_capabilities(
        agent_id="multi-agent-1",
        required_capabilities=[
            {"name": "text_processing"},
            {"name": "code_generation"}
        ],
        optional_capabilities=[
            {"name": "image_generation"}
        ]
    )
    
    print(f"Negotiation with multi-agent-1:")
    print(f"  Success: {negotiation_result['success']}")
    print(f"  Message: {negotiation_result['message']}")
    print(f"  Required capabilities: {len(negotiation_result['required_capabilities'])}")
    print(f"  Available optional capabilities: {len(negotiation_result['available_optional_capabilities'])}")
    
    # Validate data against capability schemas
    print("\n5. Validating data against capability schemas...")
    
    # Valid image generation request
    valid_image_data = {
        "prompt": "A beautiful sunset over the ocean",
        "width": 512,
        "height": 512,
        "style": "realistic"
    }
    
    is_valid, error = await capabilities_registry.validate_capability(
        name="image_generation",
        version="1.0.0",
        data=valid_image_data
    )
    
    print(f"Validating image generation data:")
    print(f"  Data: {json.dumps(valid_image_data)}")
    print(f"  Valid: {is_valid}")
    if error:
        print(f"  Error: {error}")
    
    # Invalid image generation request
    invalid_image_data = {
        "prompt": "A beautiful sunset over the ocean",
        "width": 2048,  # Exceeds maximum
        "style": "watercolor"  # Not in enum
    }
    
    is_valid, error = await capabilities_registry.validate_capability(
        name="image_generation",
        version="1.0.0",
        data=invalid_image_data
    )
    
    print(f"\nValidating invalid image generation data:")
    print(f"  Data: {json.dumps(invalid_image_data)}")
    print(f"  Valid: {is_valid}")
    if error:
        print(f"  Error: {error}")
    
    # Update agent status
    print("\n6. Updating agent status...")
    
    # Update the status of text-agent-1
    await discovery_service.update_agent_status(
        agent_id="text-agent-1",
        status="busy"
    )
    
    # Get the updated agent
    agent = await discovery_service.get_agent(
        agent_id="text-agent-1"
    )
    
    print(f"Updated status of {agent['name']}:")
    print(f"  Status: {agent['status']}")
    print(f"  Last heartbeat: {agent['last_heartbeat']}")
    
    # Send a heartbeat
    print("\n7. Sending agent heartbeats...")
    
    # Send a heartbeat for image-agent-1
    await discovery_service.heartbeat(
        agent_id="image-agent-1",
        status="idle",
        metadata={
            "current_task": None,
            "available_memory": "8GB",
            "available_gpu": "16GB"
        }
    )
    
    # Get the updated agent
    agent = await discovery_service.get_agent(
        agent_id="image-agent-1"
    )
    
    print(f"Sent heartbeat for {agent['name']}:")
    print(f"  Status: {agent['status']}")
    print(f"  Last heartbeat: {agent['last_heartbeat']}")
    print(f"  Metadata: {json.dumps(agent['metadata'])}")
    
    print("\nExample completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
