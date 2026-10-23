from app.application.alert_pipeline import AlertPipelineService
from app.adapters.postgres_incident_repository import PostgresIncidentRepository
from app.application.investigation import InvestigationService
from app.application.simulator import simulator_service
from app.adapters.postgres_investigation_repository import PostgresInvestigationRepository
from app.application.job_queue import JobRepository


alert_pipeline_service = AlertPipelineService(PostgresIncidentRepository())
investigation_service = InvestigationService(
    alert_pipeline_service,
    simulator_service,
    PostgresInvestigationRepository(),
    jobs=JobRepository(),
)
