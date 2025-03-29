graph TD
    classDef phase fill:#f9f,stroke:#333,stroke-width:2px
    classDef component fill:#bbf,stroke:#333,stroke-width:1px
    classDef criteria fill:#bfb,stroke:#333,stroke-width:1px
    classDef rollback fill:#fbb,stroke:#333,stroke-width:1px

    %% Main Phases
    P1[Phase 1: Foundation and Critical Components] --> P2[Phase 2: Core Functionality Migration]
    P2 --> P3[Phase 3: User-Facing Components Migration]
    P3 --> P4[Phase 4: Complete Migration and Legacy Retirement]
    
    %% Phase 1 Details
    P1 --> P1C1[Infrastructure Setup]
    P1 --> P1C2[Core Components]
    P1 --> P1C3[MCP Server Integration]
    P1 --> P1C4[Task Manager Integration]
    
    %% Phase 1 Success Criteria
    P1 --> P1S[Success Criteria]
    P1S --> P1S1[All unit tests pass]
    P1S --> P1S2[Integration tests successful]
    P1S --> P1S3[Performance benchmarks met]
    P1S --> P1S4[Circuit breaker functional]
    
    %% Phase 1 Rollback
    P1 --> P1R[Rollback Procedure]
    P1R --> P1R1[Revert code changes]
    P1R --> P1R2[Restore configuration]
    P1R --> P1R3[Verify functionality]
    
    %% Phase 2 Details
    P2 --> P2C1[Orchestration Engine]
    P2 --> P2C2[High-Priority Gap Solutions]
    P2 --> P2C3[Enhanced Monitoring]
    
    %% Phase 2 Success Criteria
    P2 --> P2S[Success Criteria]
    P2S --> P2S1[Orchestration tests pass]
    P2S --> P2S2[Complex workflows execute]
    P2S --> P2S3[Dashboard displays metrics]
    
    %% Phase 2 Rollback
    P2 --> P2R[Rollback Procedure]
    P2R --> P2R1[Switch to previous engine]
    P2R --> P2R2[Revert code changes]
    P2R --> P2R3[Restore Phase 1 config]
    
    %% Phase 3 Details
    P3 --> P3C1[User Interfaces]
    P3 --> P3C2[Medium-Priority Gap Solutions]
    P3 --> P3C3[Documentation and Training]
    
    %% Phase 3 Success Criteria
    P3 --> P3S[Success Criteria]
    P3S --> P3S1[UIs display workflow info]
    P3S --> P3S2[Users can manage workflows]
    P3S --> P3S3[Documentation complete]
    
    %% Phase 3 Rollback
    P3 --> P3R[Rollback Procedure]
    P3R --> P3R1[Switch to previous UI]
    P3R --> P3R2[Revert code changes]
    P3R --> P3R3[Notify users]
    
    %% Phase 4 Details
    P4 --> P4C1[Remaining Components]
    P4 --> P4C2[Low-Priority Gap Solutions]
    P4 --> P4C3[Optimization]
    
    %% Phase 4 Success Criteria
    P4 --> P4S[Success Criteria]
    P4S --> P4S1[All components migrated]
    P4S --> P4S2[All gap solutions implemented]
    P4S --> P4S3[System stable under load]
    
    %% Phase 4 Rollback
    P4 --> P4R[Rollback Procedure]
    P4R --> P4R1[Reactivate legacy components]
    P4R --> P4R2[Revert to Phase 3]
    P4R --> P4R3[Develop new migration plan]
    
    %% Apply classes
    class P1,P2,P3,P4 phase
    class P1C1,P1C2,P1C3,P1C4,P2C1,P2C2,P2C3,P3C1,P3C2,P3C3,P4C1,P4C2,P4C3 component
    class P1S,P1S1,P1S2,P1S3,P1S4,P2S,P2S1,P2S2,P2S3,P3S,P3S1,P3S2,P3S3,P4S,P4S1,P4S2,P4S3 criteria
    class P1R,P1R1,P1R2,P1R3,P2R,P2R1,P2R2,P2R3,P3R,P3R1,P3R2,P3R3,P4R,P4R1,P4R2,P4R3 rollback
