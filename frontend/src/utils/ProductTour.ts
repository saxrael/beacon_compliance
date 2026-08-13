import { driver } from "driver.js";
import "driver.js/dist/driver.css";

export const startProductTour = () => {
  const driverObj = driver({
    showProgress: true,
    animate: true,
    allowClose: true,
    overlayColor: "rgba(15, 23, 42, 0.8)",
    popoverClass: "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl",
    steps: [
      { 
        element: ".tour-header-logo", 
        popover: { 
          title: "Welcome to Beacon Compliance", 
          description: "This is your OSCR Compliance Dashboard. Let's take a quick tour to help you get started.", 
          side: "bottom", 
          align: "start" 
        } 
      },
      { 
        element: ".tour-menu-btn", 
        popover: { 
          title: "Main Menu", 
          description: "Click here to open the sidebar. You can manage your Account Settings, enable 2FA, and contact the Administrator.", 
          side: "bottom", 
          align: "center" 
        } 
      },
      { 
        element: ".tour-theme-btn", 
        popover: { 
          title: "Theme Toggle", 
          description: "Switch between light and dark modes to suit your viewing preference.", 
          side: "bottom", 
          align: "center" 
        } 
      },
      { 
        element: ".tour-help-btn", 
        popover: { 
          title: "Help & Tour", 
          description: "Need a refresher? Click this icon anytime to restart the interactive tour.", 
          side: "bottom", 
          align: "center" 
        } 
      },
      { 
        element: ".tour-dashboard-stats", 
        popover: { 
          title: "Compliance Overview", 
          description: "Here you will see the high-level metrics and your progress towards OSCR compliance deliverables.", 
          side: "top", 
          align: "start" 
        } 
      },
      { 
        element: ".tour-dashboard-actions", 
        popover: { 
          title: "Quick Actions", 
          description: "Upload financial documents, generate the R&P accounts, or chat with the AI compliance assistant from here.", 
          side: "top", 
          align: "start" 
        } 
      }
    ]
  });

  driverObj.drive();
};
