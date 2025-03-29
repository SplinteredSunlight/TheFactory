stateDiagram-v2
    [*] --> Closed
    
    Closed --> Open: Failure threshold reached
    Open --> HalfOpen: Reset timeout elapsed
    HalfOpen --> Closed: Successful operation
    HalfOpen --> Open: Failed operation
    
    state Closed {
        [*] --> Normal
        Normal --> CountingFailures: Failure occurs
        CountingFailures --> Normal: Success occurs
        CountingFailures --> [*]: Failure count < threshold
    }
    
    state Open {
        [*] --> RejectingRequests
        RejectingRequests --> [*]: Waiting for timeout
    }
    
    state HalfOpen {
        [*] --> TestingService
        TestingService --> [*]: Limited requests allowed
    }
