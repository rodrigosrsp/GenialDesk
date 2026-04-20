use serde::{Serialize, Deserialize};
use hbb_common::{
    config::Config,
    get_uuid,
    log,
    sysinfo::System,
    tokio,
};
use std::sync::atomic::{AtomicBool, Ordering};

const TELEMETRY_INTERVAL_S: u64 = 300; // 5 minutes
pub static TRUST_STATE: AtomicBool = AtomicBool::new(false);

#[derive(Serialize, Debug)]
struct Telemetry {
    agent_id: String,
    os_name: String,
    os_arch: String,
    cpu_cores: usize,
    ram_total_mb: u64,
    rustdesk_id: String,
}

#[derive(Deserialize, Debug)]
struct CheckinResponse {
    #[serde(default)]
    ok: bool,
    #[serde(default)]
    auth_required: bool,
    action: Option<String>,
}

fn gather_telemetry() -> Telemetry {
    let mut sys = System::new();
    sys.refresh_memory();
    sys.refresh_cpu();

    Telemetry {
        agent_id: hex::encode(get_uuid()),
        os_name: std::env::consts::OS.to_string(),
        os_arch: std::env::consts::ARCH.to_string(),
        cpu_cores: sys.cpus().len(),
        ram_total_mb: sys.total_memory() / 1024 / 1024,
        rustdesk_id: Config::get_id(),
    }
}

pub fn start_telemetry_loop() {
    tokio::spawn(async move {
        log::info!("Starting GenialDesk telemetry loop.");
        tokio::time::sleep(std::time::Duration::from_secs(60)).await;

        loop {
            let api_server = crate::get_api_server("".to_string(), "".to_string());
            if api_server.is_empty() {
                log::warn!("API server not configured. Telemetry check-in skipped.");
                TRUST_STATE.store(false, Ordering::SeqCst);
                tokio::time::sleep(std::time::Duration::from_secs(TELEMETRY_INTERVAL_S)).await;
                continue;
            }

            let checkin_url = format!("{}/api/agent/checkin", api_server);
            let telemetry_data = gather_telemetry();

            match serde_json::to_string(&telemetry_data) {
                Ok(json_body) => {
                    log::info!("Sending telemetry check-in to {}", checkin_url);
                    let header = "Authorization: Bearer genial-agent-secret";
                    match crate::post_request(checkin_url.clone(), json_body, header).await {
                        Ok(response_body) => {
                            match serde_json::from_str::<CheckinResponse>(&response_body) {
                                Ok(checkin_response) => {
                                    log::info!("Telemetry check-in response: {:?}", checkin_response);
                                    let is_trusted = checkin_response.ok && !checkin_response.auth_required;
                                    TRUST_STATE.store(is_trusted, Ordering::SeqCst);
                                    log::info!("Agent trust state set to: {}", is_trusted);

                                    if let Some(action) = checkin_response.action {
                                        if action == "force_logout" {
                                            log::warn!("Received 'force_logout' action. Closing all connections.");
                                            crate::server::CLIENT_SERVER.write().unwrap().close_connections();
                                        }
                                    }
                                }
                                Err(e) => {
                                    log::error!("Failed to parse check-in response: {}. Body: {}", e, response_body);
                                    TRUST_STATE.store(false, Ordering::SeqCst);
                                }
                            }
                        }
                        Err(e) => {
                            log::error!("Failed to send telemetry check-in to {}: {}", checkin_url, e);
                            TRUST_STATE.store(false, Ordering::SeqCst);
                        }
                    }
                }
                Err(e) => {
                    log::error!("Failed to serialize telemetry data: {}", e);
                    TRUST_STATE.store(false, Ordering::SeqCst);
                }
            }

            tokio::time::sleep(std::time::Duration::from_secs(TELEMETRY_INTERVAL_S)).await;
        }
    });
}
