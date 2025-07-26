import streamlit as st
import pandas as pd
import json
from api_handler import get_ohlcv_data, get_technical_indicators
from config import CACHE_EXPIRATION

# Cache data fetches
@st.cache_data(ttl=CACHE_EXPIRATION)
def fetch_verification_data(ticker, source):
    ohlcv = get_ohlcv_data(ticker, source)
    if ohlcv:
        indicators = get_technical_indicators(ticker, source)
        return {**ohlcv, **indicators}
    return None

def main():
    st.set_page_config(layout="wide", page_title="Ghost-Verification")
    st.title("📊 Ghost-Verification System")
    st.caption("Compare technical indicator values between verification system and GhostScore Platform")
    
    # --- GhostScore Data Input (Required First Step) ---
    st.sidebar.header("GhostScore Data Input")
    ghost_score_json = st.sidebar.text_area(
        "Paste GhostScore JSON (Required)",
        height=400,
        value="",
        help="Paste the complete JSON data from GhostScore platform before proceeding"
    )
    
    if not ghost_score_json.strip():
        st.warning("Please paste your GhostScore JSON data in the sidebar to continue")
        st.stop()
    
    try:
        ghost_score_data = json.loads(ghost_score_json)
        if not isinstance(ghost_score_data, dict):
            raise ValueError("GhostScore data should be a JSON object")
        
        # Get available tickers from the GhostScore data
        available_tickers = [k for k in ghost_score_data.keys() 
                           if isinstance(ghost_score_data[k], dict)]
        if not available_tickers:
            raise ValueError("No valid ticker data found in the JSON")
        
        # --- Ticker Selection ---
        selected_ticker = st.sidebar.selectbox(
            "Select Ticker", 
            available_tickers,
            index=0
        )
        ticker_data = ghost_score_data[selected_ticker]
        
        # --- Verification Configuration ---
        st.sidebar.header("Verification Configuration")
        api_source = st.sidebar.selectbox(
            "Data Source for Verification",
            ["alpha_vantage"],
            format_func=lambda x: x.replace("_", " ").title(),
            index=0
        )
        
        # --- Fetch Verification Data ---
        with st.spinner(f"Fetching verification data for {selected_ticker}..."):
            verification_data = fetch_verification_data(selected_ticker, api_source)
            if not verification_data:
                st.error("Failed to fetch verification data")
                st.stop()
            
            # Convert to dataframes
            df_base = pd.DataFrame(
                [(k, v) for k, v in verification_data.items()],
                columns=["Indicator", "Verification App"]
            )
            
            df_comp = pd.DataFrame(
                [(k, v) for k, v in ticker_data.items()],
                columns=["Indicator", "GhostScore Platform"]
            )
            
            # --- Comparison Logic ---
            comparison_df = pd.merge(
                df_base, 
                df_comp, 
                on="Indicator", 
                how="outer",
                suffixes=(" (Verification)", " (GhostScore)")
            )
            
            def highlight_diff(row):
                try:
                    val1 = row["Verification App"]
                    val2 = row["GhostScore Platform"]
                    
                    if pd.isna(val1):
                        return "🔴 Missing in Verification"
                    if pd.isna(val2):
                        return "🔵 Missing in GhostScore"
                    
                    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                        diff = val1 - val2
                        pct_diff = (diff / val1) * 100 if val1 != 0 else 0
                        
                        if abs(pct_diff) > 1.0:  # 1% threshold
                            direction = "🔺" if diff > 0 else "🔻"
                            return f"{direction} {abs(pct_diff):.2f}%"
                        return "✅ Within 1%"
                    
                    # For non-numeric comparison
                    return "✅ Match" if val1 == val2 else "⚠️ Different"
                
                except Exception:
                    return "⚪ N/A"
            
            comparison_df["Difference"] = comparison_df.apply(highlight_diff, axis=1)
            
            # --- Display Results ---
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"🔍 Verification Data")
                st.dataframe(
                    df_base,
                    height=700,
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                st.subheader("📱 GhostScore Data")
                st.dataframe(
                    df_comp,
                    height=700,
                    use_container_width=True,
                    hide_index=True
                )
            
            # --- Differences Analysis ---
            st.subheader("🔎 Differences Analysis")
            
            # Metrics
            diff_stats = comparison_df["Difference"].value_counts().to_dict()
            
            cols = st.columns(4)
            cols[0].metric("Total Indicators", len(comparison_df))
            cols[1].metric("Matching Indicators", 
                          diff_stats.get("✅ Within 1%", 0) + 
                          diff_stats.get("✅ Match", 0))
            cols[2].metric("Significant Differences", 
                          diff_stats.get("🔺", 0) + 
                          diff_stats.get("🔻", 0))
            cols[3].metric("Missing Indicators", 
                         diff_stats.get("🔴 Missing in Verification", 0) + 
                         diff_stats.get("🔵 Missing in GhostScore", 0))
            
            # Detailed differences
            st.dataframe(
                comparison_df,
                height=500,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Difference": st.column_config.Column(
                        width="medium",
                        help="Verification vs GhostScore comparison"
                    )
                }
            )
            
            # --- Download Options ---
            st.download_button(
                label="📥 Download Full Comparison (CSV)",
                data=comparison_df.to_csv(index=False).encode('utf-8'),
                file_name=f"{selected_ticker}_comparison.csv",
                mime='text/csv'
            )
    
    except json.JSONDecodeError:
        st.error("Invalid JSON format. Please check your input and try again.")
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")

if __name__ == "__main__":
    main()