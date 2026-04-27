use once_cell::sync::Lazy;

pub struct SelectionConfig {
    pub core_budget_fraction: f64,
    pub r_cap_min: f64,
    pub stopping_threshold: f64,
}

impl Default for SelectionConfig {
    fn default() -> Self {
        Self {
            core_budget_fraction: 0.70,
            r_cap_min: 0.01,
            stopping_threshold: 0.08,
        }
    }
}

pub struct RescueConfig {
    pub budget_fraction: f64,
    pub min_score_percentile: f64,
}

impl Default for RescueConfig {
    fn default() -> Self {
        Self {
            budget_fraction: 0.05,
            min_score_percentile: 0.80,
        }
    }
}

pub struct BoltzmannConfig {
    pub beta_lo: f64,
    pub beta_hi: f64,
    pub bisect_iters: u32,
    pub calibration_tolerance: f64,
}

impl Default for BoltzmannConfig {
    fn default() -> Self {
        Self {
            beta_lo: 1e-6,
            beta_hi: 1.0,
            bisect_iters: 24,
            calibration_tolerance: 0.05,
        }
    }
}

pub static SELECTION: Lazy<SelectionConfig> = Lazy::new(SelectionConfig::default);
pub static RESCUE: Lazy<RescueConfig> = Lazy::new(RescueConfig::default);
pub static BOLTZMANN: Lazy<BoltzmannConfig> = Lazy::new(BoltzmannConfig::default);
