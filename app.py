"""
AI Code Quality Reviewer - Streamlit Web Application

A web-based code review tool that combines rule-based analysis with AI-powered insights.
Uses OpenAI's GPT models to provide intelligent, context-aware code reviews.

Run with: streamlit run app.py
"""
import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our utilities
from src.streamlit_utils import (
    format_severity_with_color,
    format_issue_for_display,
    group_issues_by_severity,
    group_issues_by_category,
    generate_summary_dict,
    get_quality_score_color,
    validate_code_input,
    validate_language_selection,
    run_review,
    export_to_json,
    export_to_markdown,
    export_to_csv,
    get_review_mode_config,
    build_config_from_ui_inputs
)
from src.models.review_models import Severity


# Page configuration
st.set_page_config(
    page_title="AI Code Quality Reviewer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Header
# ============================================================================

st.markdown('<h1 class="main-header">🔍 AI Code Quality Reviewer</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Hybrid code review combining rule-based analysis with AI-powered insights</p>', unsafe_allow_html=True)


# ============================================================================
# Sidebar - Configuration
# ============================================================================

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Review mode selection
    st.subheader("Review Mode")
    review_mode = st.radio(
        "Select review mode:",
        ["Quick Scan (Rules Only)", "Standard (Hybrid)", "Deep Analysis (AI Focus)"],
        index=1,
        help="Quick: Fast rule-based checks | Standard: Best of both | Deep: AI-powered analysis"
    )
    
    # Map display names to mode keys
    mode_map = {
        "Quick Scan (Rules Only)": "quick",
        "Standard (Hybrid)": "standard",
        "Deep Analysis (AI Focus)": "deep"
    }
    selected_mode = mode_map[review_mode]
    
    st.divider()
    
    # Advanced configuration (expandable)
    with st.expander("🔧 Advanced Settings"):
        st.subheader("Rule-Based Reviewers")
        enable_style = st.checkbox("Style Checker", value=True, help="Check naming conventions, formatting")
        enable_complexity = st.checkbox("Complexity Analyzer", value=True, help="Check cyclomatic complexity")
        enable_security = st.checkbox("Security Scanner", value=True, help="Detect hardcoded secrets, vulnerabilities")
        
        st.subheader("AI Configuration")
        enable_ai = st.checkbox("AI Reviewer", value=(selected_mode in ["standard", "deep"]), help="Use OpenAI for semantic analysis")
        
        if enable_ai:
            ai_model = st.selectbox(
                "AI Model",
                ["gpt-4o-mini", "gpt-4o", "gpt-4"],
                index=0,
                help="gpt-4o-mini: Fast & cheap | gpt-4o: Balanced | gpt-4: Most capable"
            )
            
            ai_temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="Lower = more consistent, Higher = more creative"
            )
        
        st.subheader("Complexity Settings")
        max_complexity = st.slider(
            "Max Complexity Threshold",
            min_value=1,
            max_value=20,
            value=10,
            help="Maximum allowed cyclomatic complexity"
        )
    
    st.divider()
    
    # API Key status
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        st.success("✅ OpenAI API Key Loaded")
    else:
        st.warning("⚠️ No API Key (AI reviews disabled)")
        st.info("Add OPENAI_API_KEY to your .env file to enable AI reviews")


# ============================================================================
# Main Content
# ============================================================================

# Language selection
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📝 Code Input")

with col2:
    language = st.selectbox(
        "Language",
        ["python", "javascript", "typescript"],
        index=0
    )

# Code input area
code_input = st.text_area(
    "Paste your code here:",
    height=300,
    placeholder="def example_function():\n    return 'Hello, World!'",
    help="Enter the code you want to review"
)

# Review button
col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    review_button = st.button("🚀 Run Review", type="primary", use_container_width=True)

with col2:
    clear_button = st.button("🗑️ Clear", use_container_width=True)

if clear_button:
    st.rerun()


# ============================================================================
# Review Execution
# ============================================================================

if review_button:
    # Validate input
    is_valid, error_msg = validate_code_input(code_input)
    
    if not is_valid:
        st.error(f"❌ {error_msg}")
    elif not validate_language_selection(language):
        st.error(f"❌ Unsupported language: {language}")
    else:
        # Build configuration
        if selected_mode != "custom":
            config = get_review_mode_config(selected_mode)
        else:
            # Use advanced settings
            config = build_config_from_ui_inputs({
                "enable_style": enable_style,
                "enable_complexity": enable_complexity,
                "enable_security": enable_security,
                "enable_ai": enable_ai and api_key is not None,
                "ai_model": ai_model if enable_ai else "gpt-4o-mini",
                "ai_temperature": ai_temperature if enable_ai else 0.3,
                "max_complexity": max_complexity
            })
        
        # Show progress
        with st.spinner("🔍 Reviewing your code..."):
            result = run_review(code_input, language, config)
        
        if result is None:
            st.error("❌ Review failed. Please check your code and try again.")
        else:
            # Store result in session state for export
            st.session_state['last_result'] = result
            
            # Display results
            st.success("✅ Review complete!")
            
            # ============================================================================
            # Results Summary
            # ============================================================================
            
            st.header("📊 Review Summary")
            
            summary = generate_summary_dict(result)
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                quality_color = get_quality_score_color(summary["quality_score"])
                st.metric(
                    "Quality Score",
                    f"{summary['quality_score']:.1f}/100",
                    help="Overall code quality score"
                )
            
            with col2:
                st.metric(
                    "Total Issues",
                    summary["total_issues"],
                    help="Number of issues found"
                )
            
            with col3:
                status_emoji = "✅" if summary["passed"] else "❌"
                st.metric(
                    "Status",
                    f"{status_emoji} {'PASSED' if summary['passed'] else 'FAILED'}",
                    help="Review pass/fail status"
                )
            
            with col4:
                critical_high = summary["critical_count"] + summary["high_count"]
                st.metric(
                    "Critical/High",
                    critical_high,
                    help="High priority issues"
                )
            
            # Severity breakdown
            st.subheader("Issues by Severity")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("🔴 Critical", summary["critical_count"])
            with col2:
                st.metric("🟠 High", summary["high_count"])
            with col3:
                st.metric("🟡 Medium", summary["medium_count"])
            with col4:
                st.metric("🔵 Low", summary["low_count"])
            with col5:
                st.metric("⚪ Info", summary["info_count"])
            
            st.divider()
            
            # ============================================================================
            # Detailed Issues
            # ============================================================================
            
            if result.total_issues > 0:
                st.header("🔍 Detailed Issues")
                
                # Tabs for different views
                tab1, tab2, tab3 = st.tabs(["By Severity", "By Category", "All Issues"])
                
                with tab1:
                    grouped_by_severity = group_issues_by_severity(result.issues)
                    
                    # Display issues in severity order
                    for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]:
                        if severity in grouped_by_severity:
                            issues = grouped_by_severity[severity]
                            st.subheader(f"{format_severity_with_color(severity)} ({len(issues)} issues)")
                            
                            for i, issue in enumerate(issues, 1):
                                with st.expander(f"Issue {i}: {issue.message[:80]}..."):
                                    st.write(f"**Category:** {issue.category.value.title()}")
                                    st.write(f"**Line:** {issue.line_number if issue.line_number else 'N/A'}")
                                    st.write(f"**Message:** {issue.message}")
                                    if issue.suggestion:
                                        st.info(f"💡 **Suggestion:** {issue.suggestion}")
                                    if issue.rule_id:
                                        st.caption(f"Rule ID: {issue.rule_id}")
                
                with tab2:
                    grouped_by_category = group_issues_by_category(result.issues)
                    
                    for category, issues in grouped_by_category.items():
                        st.subheader(f"{category.value.title()} ({len(issues)} issues)")
                        
                        for i, issue in enumerate(issues, 1):
                            with st.expander(f"{format_severity_with_color(issue.severity)} - {issue.message[:80]}..."):
                                st.write(f"**Line:** {issue.line_number if issue.line_number else 'N/A'}")
                                st.write(f"**Message:** {issue.message}")
                                if issue.suggestion:
                                    st.info(f"💡 **Suggestion:** {issue.suggestion}")
                
                with tab3:
                    for i, issue in enumerate(result.issues, 1):
                        with st.expander(f"{i}. {format_severity_with_color(issue.severity)} - {issue.category.value.title()} - {issue.message[:60]}..."):
                            st.write(f"**Line:** {issue.line_number if issue.line_number else 'N/A'}")
                            st.write(f"**Message:** {issue.message}")
                            if issue.suggestion:
                                st.info(f"💡 **Suggestion:** {issue.suggestion}")
                            if issue.rule_id:
                                st.caption(f"Rule ID: {issue.rule_id}")
            else:
                st.success("🎉 No issues found! Your code looks great!")
            
            # ============================================================================
            # Export Options
            # ============================================================================
            
            st.divider()
            st.header("💾 Export Results")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                json_export = export_to_json(result)
                st.download_button(
                    label="📄 Download JSON",
                    data=json_export,
                    file_name="code_review_results.json",
                    mime="application/json"
                )
            
            with col2:
                markdown_export = export_to_markdown(result)
                st.download_button(
                    label="📝 Download Markdown",
                    data=markdown_export,
                    file_name="code_review_results.md",
                    mime="text/markdown"
                )
            
            with col3:
                csv_export = export_to_csv(result)
                st.download_button(
                    label="📊 Download CSV",
                    data=csv_export,
                    file_name="code_review_results.csv",
                    mime="text/csv"
                )


# ============================================================================
# Footer
# ============================================================================

st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>🔍 <strong>AI Code Quality Reviewer</strong> | Built with Streamlit & OpenAI</p>
    <p>Combining rule-based analysis with AI-powered insights for comprehensive code review</p>
</div>
""", unsafe_allow_html=True)
