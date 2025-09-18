// SG D&T AI Co-Pilot - Simplified Frontend JavaScript

class AICopilot {
  constructor() {
    this.socket = io();
    this.sessionId = null;
    this.isProcessing = false;
    this.currentMode = "conversational";

    this.initializeEventListeners();
    this.initializeSocketHandlers();
  }

  initializeEventListeners() {
    // Mode toggle
    document.querySelectorAll('input[name="mode"]').forEach((radio) => {
      radio.addEventListener("change", (e) => {
        this.switchMode(e.target.value);
      });
    });

    // Chat interface
    document
      .getElementById("send-message-btn")
      .addEventListener("click", () => {
        this.sendMessage();
      });

    document.getElementById("chat-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Analysis interface
    document
      .getElementById("startConsultation")
      .addEventListener("click", () => {
        this.startConsultation();
      });

    // Export results
    document.getElementById("exportResults").addEventListener("click", () => {
      this.exportResults();
    });
  }

  initializeSocketHandlers() {
    this.socket.on("connect", () => {
      console.log("Connected to server");
      this.sessionId = this.socket.id;
    });

    this.socket.on("disconnect", () => {
      console.log("Disconnected from server");
    });

    this.socket.on("conversation_response", (data) => {
      this.handleConversationResponse(data);
    });

    this.socket.on("analysis_complete", (data) => {
      this.handleAnalysisComplete(data);
    });

    this.socket.on("progress_update", (data) => {
      this.updateProgress(data);
    });

    this.socket.on("error", (error) => {
      this.handleError(error);
    });
  }

  switchMode(mode) {
    this.currentMode = mode;

    const conversationalInterface = document.getElementById(
      "conversational-interface"
    );
    const analysisInterface = document.getElementById("analysis-interface");

    if (mode === "conversational") {
      conversationalInterface.style.display = "block";
      analysisInterface.style.display = "none";
    } else {
      conversationalInterface.style.display = "none";
      analysisInterface.style.display = "block";
    }
  }

  sendMessage() {
    const input = document.getElementById("chat-input");
    const message = input.value.trim();

    if (!message || this.isProcessing) return;

    // Add user message to chat
    this.addMessage(message, "user");

    // Clear input
    input.value = "";

    // Set processing state
    this.isProcessing = true;
    this.updateConversationStatus("AI is thinking...");

    // Send to server
    this.socket.emit("send_message", {
      message: message,
      session_id: this.sessionId,
      mode: this.currentMode,
    });
  }

  startConsultation() {
    const input = document.getElementById("clientInput");
    const content = input.value.trim();

    if (!content || this.isProcessing) return;

    // Show progress modal
    this.showProgressModal();

    // Set processing state
    this.isProcessing = true;

    // Send to server
    this.socket.emit("start_analysis", {
      content: content,
      session_id: this.sessionId,
    });
  }

  addMessage(content, sender) {
    const messagesContainer = document.getElementById("chat-messages");
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}-message`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.innerHTML =
      sender === "user"
        ? '<i class="fas fa-user"></i>'
        : '<i class="fas fa-robot"></i>';

    const messageContent = document.createElement("div");
    messageContent.className = "message-content";

    // Format content (basic markdown-like formatting)
    const formattedContent = this.formatMessage(content);
    messageContent.innerHTML = formattedContent;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  formatMessage(content) {
    // Basic formatting for better display
    return content
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/\n/g, "<br>")
      .replace(/^• (.*$)/gm, "<li>$1</li>")
      .replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");
  }

  handleConversationResponse(data) {
    this.isProcessing = false;
    this.updateConversationStatus(
      "Ready to help with your business challenges"
    );

    // Debug: Log the entire response data
    console.log("🔍 Full response data:", data);
    console.log("🔍 Recommended services:", data.recommended_services);
    console.log("🔍 Metadata:", data.metadata);

    if (data.response) {
      this.addMessage(data.response, "ai");
    }

    // Display recommended services if available
    if (data.recommended_services && data.recommended_services.length > 0) {
      console.log("✅ Displaying services:", data.recommended_services);
      this.displayRecommendedServices(data.recommended_services);
    } else if (
      data.metadata &&
      data.metadata.recommended_services &&
      data.metadata.recommended_services.length > 0
    ) {
      console.log(
        "✅ Displaying services from metadata:",
        data.metadata.recommended_services
      );
      this.displayRecommendedServices(data.metadata.recommended_services);
    } else {
      console.log("❌ No services found in response");
    }

    if (data.error) {
      this.addMessage(
        "I apologize, but I encountered an error. Please try again.",
        "ai"
      );
    }
  }

  handleAnalysisComplete(data) {
    this.isProcessing = false;
    this.hideProgressModal();

    if (data.results) {
      this.showResultsModal(data.results);
    } else if (data.error) {
      this.handleError(data.error);
    }
  }

  updateProgress(data) {
    const progressBar = document.getElementById("progressBar");
    const currentStage = document.getElementById("currentStage");

    if (progressBar) {
      progressBar.style.width = `${data.progress}%`;
      progressBar.textContent = `${data.progress}%`;
    }

    if (currentStage && data.stage) {
      currentStage.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${data.stage}`;
    }
  }

  updateConversationStatus(status) {
    const statusElement = document.getElementById("conversation-phase");
    if (statusElement) {
      statusElement.textContent = status;
    }
  }

  showProgressModal() {
    const modal = new bootstrap.Modal(document.getElementById("progressModal"));
    modal.show();
  }

  hideProgressModal() {
    const modal = bootstrap.Modal.getInstance(
      document.getElementById("progressModal")
    );
    if (modal) {
      modal.hide();
    }
  }

  showResultsModal(results) {
    const resultsContent = document.getElementById("resultsContent");
    resultsContent.innerHTML = this.formatResults(results);

    const modal = new bootstrap.Modal(document.getElementById("resultsModal"));
    modal.show();
  }

  formatResults(results) {
    // Format the results for display in the modal
    let html = '<div class="results-content">';

    if (results.final_presentation) {
      html += `<div class="result-section">
        <h5><i class="fas fa-file-alt me-2"></i>Final Presentation</h5>
        <div class="result-content">${this.formatMessage(
          results.final_presentation
        )}</div>
      </div>`;
    }

    if (results.service_recommendations) {
      html += `<div class="result-section">
        <h5><i class="fas fa-bullseye me-2"></i>Service Recommendations</h5>
        <div class="result-content">${this.formatMessage(
          results.service_recommendations
        )}</div>
      </div>`;
    }

    if (results.pricing_estimates) {
      html += `<div class="result-section">
        <h5><i class="fas fa-calculator me-2"></i>Pricing Estimates</h5>
        <div class="result-content">${this.formatMessage(
          results.pricing_estimates
        )}</div>
      </div>`;
    }

    html += "</div>";
    return html;
  }

  exportResults() {
    const resultsContent = document.getElementById("resultsContent").innerText;
    const blob = new Blob([resultsContent], { type: "text/plain" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dt-analysis-${new Date().toISOString().split("T")[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }

  displayRecommendedServices(services) {
    console.log("🎨 Displaying services:", services);

    const messagesContainer = document.getElementById("chat-messages");
    const servicesDiv = document.createElement("div");
    servicesDiv.className = "message ai-message services-message";

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.innerHTML = '<i class="fas fa-robot"></i>';

    const messageContent = document.createElement("div");
    messageContent.className = "message-content";

    let servicesHTML = '<div class="recommended-services">';
    servicesHTML +=
      '<h5><i class="fas fa-bullseye me-2"></i>Recommended Services</h5>';

    services.forEach((service, index) => {
      console.log(`🔍 Processing service ${index + 1}:`, service);
      servicesHTML += `
        <div class="service-card">
          <div class="service-header">
            <h6 class="service-name">${service.service_name || "Service"}</h6>
            <span class="service-confidence">Confidence: ${Math.round(
              (service.confidence || 0.8) * 100
            )}%</span>
          </div>
          <div class="service-description">${
            service.description || "No description available"
          }</div>
          
          ${
            service.refined_estimates
              ? `
            <div class="service-estimates">
              <h6>Project Estimates:</h6>
              <div class="estimates-grid">
                ${
                  service.refined_estimates.duration
                    ? `<div class="estimate-item"><i class="fas fa-clock"></i> Duration: ${service.refined_estimates.duration}</div>`
                    : ""
                }
                ${
                  service.refined_estimates.team_size
                    ? `<div class="estimate-item"><i class="fas fa-users"></i> Team Size: ${service.refined_estimates.team_size}</div>`
                    : ""
                }
                ${
                  service.refined_estimates.pricing_range
                    ? `<div class="estimate-item"><i class="fas fa-dollar-sign"></i> Pricing: ${service.refined_estimates.pricing_range}</div>`
                    : ""
                }
              </div>
            </div>
          `
              : ""
          }
          
          ${
            service.scope_assumptions &&
            Array.isArray(service.scope_assumptions) &&
            service.scope_assumptions.length > 0
              ? `
              <div class="scope-assumptions">
                <h6>Scope Assumptions:</h6>
                <ul>
                  ${service.scope_assumptions
                    .map((assumption) => `<li>${assumption}</li>`)
                    .join("")}
                </ul>
              </div>
            `
              : service.scope_assumptions &&
                typeof service.scope_assumptions === "string"
              ? `
              <div class="scope-assumptions">
                <h6>Scope Assumptions:</h6>
                <p>${service.scope_assumptions}</p>
              </div>
            `
              : ""
          }
          
          ${
            service.next_steps &&
            Array.isArray(service.next_steps) &&
            service.next_steps.length > 0
              ? `
              <div class="next-steps">
                <h6>Next Steps:</h6>
                <ul>
                  ${service.next_steps
                    .map((step) => `<li>${step}</li>`)
                    .join("")}
                </ul>
              </div>
            `
              : service.next_steps && typeof service.next_steps === "string"
              ? `
              <div class="next-steps">
                <h6>Next Steps:</h6>
                <p>${service.next_steps}</p>
              </div>
            `
              : ""
          }
        </div>
      `;
    });

    servicesHTML += "</div>";
    messageContent.innerHTML = servicesHTML;

    servicesDiv.appendChild(avatar);
    servicesDiv.appendChild(messageContent);
    messagesContainer.appendChild(servicesDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  handleError(error) {
    this.isProcessing = false;
    this.hideProgressModal();
    this.updateConversationStatus(
      "Ready to help with your business challenges"
    );

    console.error("Error:", error);

    const errorMessage =
      typeof error === "string"
        ? error
        : "An unexpected error occurred. Please try again.";
    this.addMessage(
      `I apologize, but I encountered an error: ${errorMessage}`,
      "ai"
    );
  }
}

// Initialize the application when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new AICopilot();
});
