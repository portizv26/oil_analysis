erDiagram
  %% =====================
  %% ASSET & SITE
  %% =====================
  SITE ||--o{ UNIT : has
  SYSTEM ||--o{ SUBSYSTEM : contains
  SUBSYSTEM ||--o{ COMPONENT : contains
  UNIT ||--o{ UNIT_COMPONENT : has
  COMPONENT ||--o{ UNIT_COMPONENT : is_installed_in

  %% =====================
  %% TECHNIQUE REGISTRY
  %% =====================
  TECHNIQUE ||--o{ TECHNIQUE_VARIABLE : defines
  TECHNIQUE_VARIABLE ||--o{ VARIABLE_LIMIT : bounded_by

  %% =====================
  %% MEASUREMENTS (SUPERTYPE)
  %% =====================
  TECHNIQUE ||--o{ MEASUREMENT : taken_by
  TECHNIQUE_VARIABLE ||--o{ MEASUREMENT : measures
  UNIT ||--o{ MEASUREMENT : on
  COMPONENT ||--o{ MEASUREMENT : context
  MEASUREMENT ||--|| MEASUREMENT_OIL : specializes
  MEASUREMENT ||--|| MEASUREMENT_TELEMETRY : specializes

  %% =====================
  %% ALERTS & CASES
  %% =====================
  TECHNIQUE ||--o{ TECHNIQUE_ALERT : within
  UNIT ||--o{ TECHNIQUE_ALERT : raises
  COMPONENT ||--o{ TECHNIQUE_ALERT : located_on

  ALERT_CASE ||--o{ ALERT_CASE_TECH_ALERT : maps
  TECHNIQUE_ALERT ||--o{ ALERT_CASE_TECH_ALERT : linked_into
  ALERT_CASE ||--o{ AI_COMMENT : has

  %% =====================
  %% COMMENTS & EVIDENCE
  %% =====================
  AI_COMMENT ||--o{ COMMENT_EVIDENCE : cites
  AI_COMMENT ||--o{ COMMENT_TAG : labeled_by

  %% =====================
  %% REVIEWS
  %% =====================
  REVIEWER ||--o{ REVIEW : writes
  AI_COMMENT ||--o{ REVIEW : evaluated_by
  REVIEW ||--o{ REVIEW_SCORE : scored_on
  RUBRIC_DIMENSION ||--o{ REVIEW_SCORE : dimensioned_by
  AI_COMMENT ||--o{ REVIEW_ADJUDICATION : may_be_adjudicated

  %% =====================
  %% LOOKUPS
  %% =====================
  COMMENT_TYPE_LU ||--o{ AI_COMMENT : types
  BREACH_LEVEL_LU ||--o{ MEASUREMENT : classifies

  %% ======= ATTR NOTES (optional, for readers) =======
  SITE { int site_id PK
        string name
        string timezone }
  UNIT { string unit_id PK
         int site_id FK }
  SYSTEM { int system_id PK }
  SUBSYSTEM { int subsystem_id PK
              int system_id FK }
  COMPONENT { int component_id PK
              int subsystem_id FK }
  UNIT_COMPONENT { int unit_component_id PK
                   string unit_id FK
                   int component_id FK }
  TECHNIQUE { int technique_id PK
              string code }
  TECHNIQUE_VARIABLE { int technique_variable_id PK
                       int technique_id FK
                       string code }
  VARIABLE_LIMIT { int variable_limit_id PK
                   int technique_variable_id FK
                   decimal threshold_value }
  MEASUREMENT { bigint measurement_id PK
                int technique_id FK
                int technique_variable_id FK
                string unit_id FK
                int component_id FK
                datetime ts
                decimal value
                bool is_limit_reached
                string breach_level }
  MEASUREMENT_OIL { bigint measurement_id PK/FK
                    date sample_date
                    decimal oil_meter }
  MEASUREMENT_TELEMETRY { bigint measurement_id PK/FK
                          decimal component_meter
                          string agg_fn }
  TECHNIQUE_ALERT { bigint technique_alert_id PK
                    int technique_id FK
                    string unit_id FK
                    int component_id FK
                    datetime start_ts
                    datetime end_ts }
  ALERT_CASE { bigint alert_case_id PK
               string unit_id FK
               int component_id FK
               datetime time_start
               string label }
  ALERT_CASE_TECH_ALERT { bigint alert_case_id FK
                          bigint technique_alert_id FK }
  AI_COMMENT { bigint ai_comment_id PK
               bigint alert_case_id FK
               text comment_text
               string comment_type FK
               char(64) content_hash
               bool active }
  COMMENT_EVIDENCE { bigint comment_evidence_id PK
                     bigint ai_comment_id FK
                     bigint technique_alert_id FK
                     bigint measurement_id FK
                     datetime window_start
                     datetime window_end }
  COMMENT_TAG { bigint comment_tag_id PK
                bigint ai_comment_id FK
                string tag }
  REVIEWER { int reviewer_id PK
             string display_name
             string email }
  RUBRIC_DIMENSION { int rubric_dimension_id PK
                     string code
                     int scale_min
                     int scale_max }
  REVIEW { bigint review_id PK
           bigint ai_comment_id FK
           int reviewer_id FK
           datetime created_at
           string overall_label
           text free_text_feedback
           text proposed_rewrite }
  REVIEW_SCORE { bigint review_score_id PK
                 bigint review_id FK
                 int rubric_dimension_id FK
                 numeric score }
  REVIEW_ADJUDICATION { bigint adjudication_id PK
                        bigint ai_comment_id FK
                        int adjudicator_id FK
                        datetime created_at
                        string final_decision }

  %% =====================
  %% STYLES
  %% =====================
  classDef asset fill:#E3F2FD,stroke:#64B5F6,color:#0D47A1,stroke-width:1px;
  classDef registry fill:#E8F5E9,stroke:#81C784,color:#1B5E20,stroke-width:1px;
  classDef measurement fill:#FFF3E0,stroke:#FFB74D,color:#E65100,stroke-width:1px;
  classDef alert fill:#FCE4EC,stroke:#F06292,color:#880E4F,stroke-width:1px;
  classDef comment fill:#EDE7F6,stroke:#9575CD,color:#311B92,stroke-width:1px;
  classDef review fill:#F3E5F5,stroke:#BA68C8,color:#4A148C,stroke-width:1px;
  classDef lookup fill:#F5F5F5,stroke:#BDBDBD,color:#424242,stroke-width:1px;

  class SITE,UNIT,SYSTEM,SUBSYSTEM,COMPONENT,UNIT_COMPONENT asset;
  class TECHNIQUE,TECHNIQUE_VARIABLE,VARIABLE_LIMIT registry;
  class MEASUREMENT,MEASUREMENT_OIL,MEASUREMENT_TELEMETRY measurement;
  class TECHNIQUE_ALERT,ALERT_CASE,ALERT_CASE_TECH_ALERT alert;
  class AI_COMMENT,COMMENT_EVIDENCE,COMMENT_TAG comment;
  class REVIEWER,RUBRIC_DIMENSION,REVIEW,REVIEW_SCORE,REVIEW_ADJUDICATION review;
  class COMMENT_TYPE_LU,BREACH_LEVEL_LU lookup;

