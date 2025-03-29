# Agent Communication Circuit Breaker Integration

## Overview

This document describes the integration of the circuit breaker pattern with the agent communication module in the AI-Orchestration-Platform. The circuit breaker pattern is a design pattern used to detect failures and prevent cascading failures in distributed systems.

## Purpose

The circuit breaker pattern is implemented in the agent communication module to:

1. Prevent cascading failures when communicating with agents
2. Provide graceful degradation when agent communication fails
3. Allow the system to recover from failures automatically
4. Improve system resilience and stability

## Implementation

The circuit breaker pattern is implemented in the `AgentCommunicationManager` class in the `src/orchestrator/communication.py` file. All methods that interact with the message broker now have a `use_circuit_breaker` parameter that defaults to `True`. When enabled, the circuit breaker wraps the calls to the message broker to protect against cascading failures.

### Key Components

1. **Circuit Breaker**: The circuit breaker is initialized in the `AgentCommunicationManager` constructor and is used to wrap calls to the message broker.

2. **Error Handling**: When the circuit breaker is open, a `CircuitBreakerOpenError` is caught and converted to a `SystemError` with appropriate error codes and details.

3. **Fallback Mechanism**: When the circuit breaker is open, the system logs the error and raises a `SystemError` to inform the caller that the operation cannot be performed.

### Methods with Circuit Breaker Integration

The following methods in the `AgentCommunicationManager` class now support circuit breaker integration:

- `register_agent`: Registers an agent with the communication manager
- `unregister_agent`: Unregisters an agent from the communication manager
- `send_message`: Sends a message from one agent to another
- `get_messages`: Gets messages for an agent
- `register_delivery_callback`: Registers a callback for message delivery
- `unregister_delivery_callback`: Unregisters a callback for message delivery
- `get_agent_capabilities`: Gets the communication capabilities of an agent
- `shutdown`: Shuts down the communication manager

## Usage

To use the circuit breaker integration with the agent communication module, simply call the methods as usual. The circuit breaker is enabled by default. If you want to disable the circuit breaker for a specific call, you can set the `use_circuit_breaker` parameter to `False`.

### Example

```python
# With circuit breaker (default)
await communication_manager.send_message(
    sender_id="agent1",
    message_type=MessageType.DIRECT,
    content={"key": "value"},
    recipient_id="agent2"
)

# Without circuit breaker
await communication_manager.send_message(
    sender_id="agent1",
    message_type=MessageType.DIRECT,
    content={"key": "value"},
    recipient_id="agent2",
    use_circuit_breaker=False
)
```

## Testing

The circuit breaker integration with the agent communication module is tested in the `tests/test_agent_communication_circuit_breaker.py` file. The tests cover all methods that support circuit breaker integration and verify that the circuit breaker is used correctly.

To run the tests, use the following command:

```bash
./scripts/run_agent_communication_circuit_breaker_tests.sh
```

## Configuration

The circuit breaker is configured using the `get_circuit_breaker` function from the `src/orchestrator/circuit_breaker.py` file. The circuit breaker is initialized with the name "agent_communication" to identify it in logs and metrics.

The circuit breaker configuration can be customized by modifying the `get_circuit_breaker` function or by providing a different circuit breaker implementation.

## Error Handling

When the circuit breaker is open, the system logs the error and raises a `SystemError` with the following details:

- **Message**: "Circuit breaker is open for agent communication: {error message}"
- **Code**: `ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN`
- **Component**: `Component.ORCHESTRATOR`
- **Severity**: `ErrorSeverity.WARNING`
- **Details**: Depends on the method being called, but typically includes the agent ID and other relevant information

## Conclusion

The circuit breaker integration with the agent communication module provides a robust mechanism for handling failures in agent communication. It helps prevent cascading failures and improves system resilience and stability.
