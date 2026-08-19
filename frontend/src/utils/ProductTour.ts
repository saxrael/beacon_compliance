import { driver } from "driver.js";
import "driver.js/dist/driver.css";

export const startProductTour = () => {
  const driverObj = driver({
    showProgress: true,
    animate: true,
    allowClose: true,
    overlayColor: "rgba(7, 10, 17, 0.85)",
    popoverClass: "beacon-tour-popover",
    nextBtnText: "Next →",
    prevBtnText: "← Back",
    doneBtnText: "Get Started ✓",
    steps: [
      { 
        element: ".tour-header-logo", 
        popover: { 
          title: "Potter's House Christian Mission UK (SC054652)", 
          description: "Welcome to Beacon Compliance — the dedicated OSCR statutory compliance portal designed for Scottish Charitable Incorporated Organisations (SCIO).", 
          side: "bottom", 
          align: "start" 
        } 
      },
      { 
        element: ".tour-menu-btn", 
        popover: { 
          title: "Trustee Governance Menu", 
          description: "Access trustee administration, update your profile credentials, or manage system provisioning.", 
          side: "bottom", 
          align: "start" 
        } 
      },
      { 
        element: ".tour-upload-center", 
        popover: { 
          title: "Financial Ingestion & Privacy Guard", 
          description: "Upload bank statements, donation schedules, or invoices. Built-in OCR parses tabular data, and privacy filters scrub sensitive account numbers before entering the ledger.", 
          side: "top", 
          align: "start" 
        } 
      },
      { 
        element: ".tour-pipeline-runner", 
        popover: { 
          title: "Autonomous Compliance Pipeline", 
          description: "Click here to run the 5-node compliance engine. It deterministically reconciles all funds (General vs. Building) and compiles OSCR-compliant narrative accounts in seconds.", 
          side: "bottom", 
          align: "start" 
        } 
      },
      { 
        element: ".tour-financial-cards", 
        popover: { 
          title: "Receipts & Payments Balances", 
          description: "Monitor Gross Receipts, Gross Payments, and Net Fund Movements. The £250,000 gross income threshold is continuously checked to safeguard R&P eligibility.", 
          side: "top", 
          align: "start" 
        } 
      },
      { 
        element: ".tour-deliverables-grid", 
        popover: { 
          title: "Four Official OSCR Deliverables", 
          description: "Review, print, and download the 4 mandatory annual filing packages: Online Annual Return (OAR), Trustees' Annual Report (TAR), R&P Accounts, and Independent Examiner (IE) Pack. Each package includes cryptographic HMAC sign-off verification.", 
          side: "top", 
          align: "start" 
        } 
      },
      { 
        element: ".tour-chat-advisor", 
        popover: { 
          title: "Statutory Intelligence Sentinel", 
          description: "Consult your dedicated OSCR compliance advisor anytime for filing deadlines, reserve policies, and Scottish charity governance questions.", 
          side: "left", 
          align: "end" 
        } 
      }
    ]
  });

  driverObj.drive();
};

