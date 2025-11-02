"""
Session state management for Streamlit UI
"""

import streamlit as st
from typing import Dict, Any, Set


def initialize_session_state():
    """Initialize session state with default values"""
    
    # Workflow state
    if 'workflow_state' not in st.session_state:
        st.session_state.workflow_state = {
            'current_stage': 'context',
            'completed_stages': set(),
            'selected_ticket': None,
            'research_results': None,
            'plan': None,
            'plan_approved': False,
            'execution_results': None,
            'summary': None
        }
    
    # Configuration state
    if 'config' not in st.session_state:
        st.session_state.config = {
            'selected_ticket_id': 'T-EX1',
            'llm_model': 'gpt-4',
            'temperature': 0.3,
            'debug_mode': False
        }
    
    # Demo data cache
    if 'demo_data_loaded' not in st.session_state:
        st.session_state.demo_data_loaded = False


def get_workflow_state() -> Dict[str, Any]:
    """Get current workflow state"""
    return st.session_state.workflow_state


def update_workflow_state(updates: Dict[str, Any]):
    """Update workflow state"""
    st.session_state.workflow_state.update(updates)


def advance_to_stage(stage: str):
    """Advance workflow to next stage"""
    current_stage = st.session_state.workflow_state['current_stage']
    
    # Add current stage to completed
    completed = st.session_state.workflow_state['completed_stages']
    if isinstance(completed, set):
        completed.add(current_stage)
    else:
        completed = {current_stage}
    
    # Update state
    st.session_state.workflow_state.update({
        'current_stage': stage,
        'completed_stages': completed
    })


def navigate_to_stage(stage: str):
    """Navigate to any stage (for backward navigation)"""
    # Get valid stages in order
    valid_stages = ['context', 'ticket_input', 'research', 'planning', 'execution', 'closing']
    current_stage = st.session_state.workflow_state['current_stage']
    completed_stages = st.session_state.workflow_state['completed_stages']
    
    # Allow navigation to completed stages or current stage
    if stage in completed_stages or stage == current_stage:
        st.session_state.workflow_state['current_stage'] = stage
        return True
    
    # Allow navigation to the next logical stage if current is completed
    if current_stage in completed_stages:
        current_index = valid_stages.index(current_stage)
        target_index = valid_stages.index(stage)
        
        # Allow navigation to next stage only
        if target_index == current_index + 1:
            st.session_state.workflow_state['current_stage'] = stage
            return True
    
    return False


def can_navigate_to_stage(stage: str) -> bool:
    """Check if navigation to a stage is allowed"""
    current_stage = st.session_state.workflow_state['current_stage']
    completed_stages = st.session_state.workflow_state['completed_stages']
    
    # Always allow navigation to completed stages or current stage
    if stage in completed_stages or stage == current_stage:
        return True
    
    # Allow navigation to next stage if current is completed
    if current_stage in completed_stages:
        valid_stages = ['context', 'ticket_input', 'research', 'planning', 'execution', 'closing']
        try:
            current_index = valid_stages.index(current_stage)
            target_index = valid_stages.index(stage)
            return target_index == current_index + 1
        except ValueError:
            return False
    
    return False


def get_stage_status(stage: str) -> str:
    """Get the status of a workflow stage"""
    current_stage = st.session_state.workflow_state['current_stage']
    completed_stages = st.session_state.workflow_state['completed_stages']
    
    if stage in completed_stages:
        return 'completed'
    elif stage == current_stage:
        return 'current'
    elif can_navigate_to_stage(stage):
        return 'available'
    else:
        return 'locked'


def reset_workflow():
    """Reset workflow to initial state"""
    st.session_state.workflow_state = {
        'current_stage': 'context',
        'completed_stages': set(),
        'selected_ticket': None,
        'research_results': None,
        'plan': None,
        'plan_approved': False,
        'execution_results': None,
        'summary': None
    }


def get_config() -> Dict[str, Any]:
    """Get current configuration"""
    return st.session_state.config


def update_config(updates: Dict[str, Any]):
    """Update configuration"""
    st.session_state.config.update(updates)


def get_selected_ticket():
    """Get currently selected ticket"""
    return st.session_state.workflow_state.get('selected_ticket')


def set_selected_ticket(ticket):
    """Set selected ticket"""
    st.session_state.workflow_state['selected_ticket'] = ticket
