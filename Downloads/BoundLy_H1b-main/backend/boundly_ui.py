from fasthtml.common import *
import uvicorn
from typing import Dict, Any

# Define the structure of the questionnaire
# This allows for easy modification and rendering of steps.
STEPS_CONFIG = {
    1: {'id': 'welcome', 'title': 'Welcome'},
    2: {'id': 'status', 'title': 'Immigration Status'},
    3: {'id': 'j1_residency', 'title': 'J-1 Requirement'},
    4: {'id': 'maintenance', 'title': 'Maintenance of Status'},
    5: {'id': 'offer', 'title': 'Job Offer & Sponsorship'},
    6: {'id': 'specialty', 'title': 'Specialty Occupation'},
    7: {'id': 'education', 'title': 'Education'},
    8: {'id': 'license', 'title': 'Licensing'},
    9: {'id': 'wage', 'title': 'Wage & Location'},
    10: {'id': 'lca', 'title': 'LCA'},
    11: {'id': 'summary', 'title': 'Summary'}
}
TOTAL_STEPS = len(STEPS_CONFIG) - 1 # Exclude welcome screen from progress

# FastHTML app setup with enhanced styling
app, rt = fast_app(
    hdrs=(
        Script(src="https://cdn.tailwindcss.com"),
        Link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=True),
        Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"),
        Style("""
            body { font-family: 'Inter', sans-serif; background-color: #f0f2f5; }
            .form-step { animation: fadeIn 0.5s ease-in-out; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            .progress-bar-fill { transition: width 0.5s ease-in-out; }
            .radio-label:has(input:checked) { background-color: #eef2ff; border-color: #818cf8; }
        """)
    )
)

def render_hidden_inputs(data: Dict[str, Any]) -> list:
    """Render hidden inputs to maintain state across requests."""
    return [Input(type='hidden', name=key, value=val) for key, val in data.items() if val is not None]

def create_progress_bar(current_step_num: int) -> Div:
    """Renders the progress bar."""
    progress_pct = (current_step_num - 1) / TOTAL_STEPS * 100
    return Div(
        Div(
            P(f"Step {current_step_num-1} of {TOTAL_STEPS}", cls="text-sm font-medium text-indigo-600"),
            Div(
                Div(cls="w-full bg-gray-200 rounded-full h-2.5"),
                Div(cls="bg-indigo-600 h-2.5 rounded-full progress-bar-fill", style=f"width: {progress_pct}%"),
                cls="relative"
            ),
            cls="flex flex-col gap-2"
        ),
        cls="mb-8"
    )

def create_navigation_buttons(current_step_num: int) -> Div:
    """Renders Back and Next buttons."""
    # The 'Back' button is a simple link to the previous step's rendering function
    # This is a simple implementation. A more robust solution might use hx-get.
    back_button = A(
        "Back",
        href="/",  # Simplistic back button, reloads for now. A better way would be hx-get to a back endpoint.
        cls="bg-gray-200 text-gray-800 font-semibold py-2 px-5 rounded-lg hover:bg-gray-300 transition"
    ) if current_step_num > 2 else Div() # No back button on the first question

    return Div(
        back_button,
        Button("Next", type="submit", cls="bg-indigo-600 text-white font-semibold py-2 px-5 rounded-lg hover:bg-indigo-700 transition"),
        cls="mt-8 flex justify-between"
    )

def create_form_wrapper(current_step_num: int, *content, **kwargs) -> Form:
    """Wraps form content with htmx attributes and hidden state."""
    return Form(
        *content,
        Input(type='hidden', name='current_step', value=current_step_num),
        *render_hidden_inputs(kwargs),
        hx_post="/next_step",
        hx_target="#h1b-checker-form",
        hx_swap="innerHTML",
        cls="form-step"
    )

# --- Step Rendering Functions ---

def render_step_1_welcome() -> Div:
    return Div(
        H1("Am I Eligible for H‑1B Status?", cls="text-3xl font-bold text-gray-800 mb-4 text-center"),
        P("The H-1B is a visa for workers in specialty occupations. This tool will help you evaluate your eligibility based on key requirements.", cls="text-gray-600 mb-6 text-center"),
        Form(
            Button("Check My Eligibility →", type="submit", cls="bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-indigo-700 transition duration-300"),
            hx_post="/next_step",
            hx_target="#h1b-checker-form",
            hx_swap="innerHTML",
            cls="text-center"
        ),
        cls="form-step"
    )

def render_step_2_status(**kwargs) -> Form:
    current_step_num = 2
    options = ["H-1B", "H-4", "F-1/F-2", "J-1/J-2", "F-1 on OPT/STEM OPT", "B-1/B-2"]
    return create_form_wrapper(
        current_step_num,
        create_progress_bar(current_step_num),
        H2("Step 1: Current Immigration Status", cls="text-2xl font-semibold text-gray-700 mb-5"),
        Fieldset(
            *[Label(
                Input(type="radio", name="status", value=opt, required=True, cls="mr-3"),
                opt,
                cls="flex items-center p-3 border rounded-lg hover:bg-gray-100 cursor-pointer radio-label"
            ) for opt in options],
            cls="space-y-3"
        ),
        create_navigation_buttons(current_step_num),
        **kwargs
    )

def render_step_3_j1_residency(**kwargs) -> Form:
    current_step_num = 3
    return create_form_wrapper(
        current_step_num,
        create_progress_bar(current_step_num),
        H2("Step 2: Two-Year Foreign Residence Requirement", cls="text-2xl font-semibold text-gray-700 mb-5"),
        P("If you are in J-1/J-2 status, are you subject to a two-year foreign residency requirement under INA 212(e)?", cls="mb-4"),
        Fieldset(
            Label(Input(type="radio", name="j1_waiver", value="yes", required=True, cls="mr-2"), "Yes", cls="p-3 border rounded-lg radio-label"),
            Label(Input(type="radio", name="j1_waiver", value="no", required=True, cls="mr-2"), "No", cls="p-3 border rounded-lg radio-label"),
            cls="flex gap-4"
        ),
        create_navigation_buttons(current_step_num),
        **kwargs
    )

# ... other step rendering functions would follow a similar pattern ...

def render_summary_page(**kwargs) -> Div:
    """Renders the final summary page based on all collected answers."""
    # Determine eligibility based on answers
    is_eligible = (
        kwargs.get('jobOffer') == 'yes' and
        kwargs.get('specialty') != 'no' and
        kwargs.get('maintainedStatus') != 'no' and
        kwargs.get('j1_waiver', 'no') == 'no'
    )
    
    # Summary Items
    summary_items = [
        ("Job Offer & Sponsorship", kwargs.get('jobOffer', 'N/A')),
        ("Specialty Occupation", kwargs.get('specialty', 'N/A')),
        ("Maintained Lawful Status", kwargs.get('maintainedStatus', 'N/A')),
        ("LCA Filed", kwargs.get('lca', 'N/A')),
    ]

    outcome_bg, outcome_text, outcome_title = (
        ("bg-green-50 border-green-200", "text-green-700", "You Appear Eligible")
        if is_eligible
        else ("bg-red-50 border-red-200", "text-red-700", "You May Not Qualify")
    )
    
    return Div(
        H2("Eligibility Summary", cls="text-3xl font-bold text-gray-800 mb-6 text-center"),
        Div(
            *[Div(
                Span(item[0], cls="font-medium text-gray-600"),
                Span(item[1].title(), cls=f"font-bold {'text-green-600' if item[1] == 'yes' else 'text-yellow-600'}"),
                cls="flex justify-between items-center py-3 border-b"
            ) for item in summary_items],
            cls="space-y-2 mb-6"
        ),
        Div(
            H3(outcome_title, cls=f"text-2xl font-bold {outcome_text}"),
            cls=f"text-center p-5 rounded-lg {outcome_bg}"
        ),
        A("Start Over", href="/", cls="mt-8 block w-full text-center bg-gray-500 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-600 transition"),
        cls="form-step"
    )

def render_ineligible_page(title: str, message: str) -> Div:
    """Renders a generic 'ineligible' or 'warning' screen."""
    return Div(
        H2(title, cls="text-2xl font-bold text-yellow-700 mb-4 text-center"),
        P(message, cls="text-gray-600 mb-6 text-center"),
        A("Start Over", href="/", cls="mt-4 block w-full text-center bg-gray-500 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-600 transition"),
        cls="form-step p-8 bg-yellow-50 border border-yellow-200 rounded-lg"
    )

# --- Routing ---

@rt("/")
async def homepage():
    """Serves the initial page."""
    return Html(
        Head(
            Title("H-1B Eligibility Checker"),
            Script(src="https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js"),
            *app.hdrs
        ),
        Body(
            Div(
                Div(id="h1b-checker-form", cont=render_step_1_welcome()),
                cls="bg-white p-8 rounded-xl shadow-lg w-full max-w-2xl mx-auto my-12"
            )
        )
    )

@rt("/next_step", methods=["POST"])
async def next_step(data: dict):
    """The main logic controller for the multi-step form."""
    current_step = int(data.get('current_step', 1))
    
    # Store all incoming data
    all_answers = data.copy()

    # --- Logic to determine the next step ---
    if current_step == 1: # From Welcome
        return render_step_2_status(**all_answers)
    
    if current_step == 2: # From Status
        if data.get('status') == 'J-1/J-2':
            return render_step_3_j1_residency(**all_answers)
        else:
            # This is a simplification. We'd need to render step 4 here.
            # For this example, we'll just show the summary for brevity.
            return render_summary_page(**all_answers)

    if current_step == 3: # From J-1 Waiver
        if data.get('j1_waiver') == 'yes':
            return render_ineligible_page(
                "Waiver Required",
                "To qualify for H-1B, you must first obtain a waiver of the two-year foreign residence requirement."
            )
        else:
            # This is a simplification. We'd need to render step 4 here.
            return render_summary_page(**all_answers)
            
    # Default to summary for this example
    return render_summary_page(**all_answers)

if __name__ == "__main__":
    uvicorn.run("boundly_ui:app", host="0.0.0.0", port=8000, reload=True)
