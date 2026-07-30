// Set window.__API_BASE__ before loading this file when the frontend is hosted elsewhere.
const configuredApiBase = new URLSearchParams(window.location.search).get("api_base");
const API_BASE = window.__API_BASE__ || configuredApiBase || (window.location.port === "8765" ? "" : "http://127.0.0.1:8765");

const navItems = [
  { id: "chat", label: "Trò chuyện", icon: "message" },
  { id: "faq", label: "FAQ", icon: "help" },
  { id: "admission", label: "Điều kiện tuyển sinh", icon: "clipboard" },
  { id: "program", label: "Chương trình đào tạo", icon: "graduation" },
  { id: "benefits", label: "Quyền lợi", icon: "gift" },
  { id: "schedule", label: "Lịch tuyển sinh", icon: "calendar" },
  { id: "application", label: "Hồ sơ & đăng ký", icon: "file" },
  { id: "career", label: "Cơ hội việc làm", icon: "briefcase" },
  { id: "posts", label: "Bài viết & Hỏi đáp", icon: "newspaper" },
  { id: "feedback", label: "Phản hồi học viên", icon: "feedback" },
  { id: "contact", label: "Liên hệ", icon: "phone" },
];

function icon(name, className = "ui-icon") {
  const paths = {
    message: '<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/><path d="M8 9h8M8 13h5"/>',
    help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.7 2.7 0 1 1 4.2 2.2c-1 .7-1.7 1.2-1.7 2.3M12 17h.01"/>',
    clipboard: '<rect width="14" height="17" x="5" y="4" rx="2"/><path d="M9 4V2h6v2M9 12l2 2 4-4"/>',
    graduation: '<path d="m2 10 10-5 10 5-10 5z"/><path d="M6 12v5c3 2 9 2 12 0v-5M22 10v6"/>',
    gift: '<rect width="18" height="14" x="3" y="8" rx="2"/><path d="M12 8v14M3 12h18M7.5 8C5 8 5 4 7.5 4 10 4 12 8 12 8M16.5 8C19 8 19 4 16.5 4 14 4 12 8 12 8"/>',
    calendar: '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M8 14h.01M12 14h.01M16 14h.01"/>',
    file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M12 18v-6M9 15l3-3 3 3"/>',
    briefcase: '<rect width="20" height="14" x="2" y="7" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M2 12h20M10 12v2h4v-2"/>',
    newspaper: '<path d="M4 22h15a2 2 0 0 0 2-2V4H8v16a2 2 0 0 1-4 0V6H2v14a2 2 0 0 0 2 2z"/><path d="M12 8h5M12 12h5M12 16h5"/>',
    feedback: '<path d="M20 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h9a4 4 0 0 1 4 4z"/><path d="m8 11 2 2 4-4"/>',
    phone: '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.5 2.1L8 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.7 2z"/>',
    map: '<path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0z"/><circle cx="12" cy="10" r="2.5"/>',
    mail: '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-10 6L2 7"/>',
    upload: '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M20 15v5H4v-5"/>',
    star: '<path d="m12 2 3 6 7 .9-5 4.8 1.3 6.8L12 17l-6.3 3.5L7 13.7 2 8.9 9 8z"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    check: '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/>',
  };
  return `<svg class="${className}" viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.help}</svg>`;
}

const sources = [
  ["Điều kiện tuyển sinh AI Thực Chiến K1", "vinuni.edu.vn"],
  ["Thông tin tuyển sinh AI Thực Chiến", "vinuni.edu.vn"],
  ["Câu hỏi thường gặp về AI Thực Chiến", "vinuni.edu.vn"],
  ["Hỏi đáp trên cộng đồng học viên", "facebook.com"],
];

const topics = [
  "Điều kiện & Đăng ký",
  "Bài test đầu vào",
  "Chương trình & Học tập",
  "Học phí & Phụ cấp",
  "Cơ hội nghề nghiệp",
];

const pages = {
  faq: {
    title: "FAQ",
    intro: "Những câu hỏi tuyển sinh thường gặp được gom theo chủ đề để đội tư vấn và học viên kiểm tra nhanh.",
    body: faqPage,
  },
  admission: {
    title: "Điều kiện tuyển sinh",
    intro: "Các điều kiện nền tảng giúp ứng viên tự đánh giá trước khi đăng ký.",
    body: admissionPage,
  },
  program: {
    title: "Chương trình đào tạo",
    intro: "Lộ trình AI Thực Chiến được chia thành nền tảng, thực hành và demo cuối khoá.",
    body: programPage,
  },
  benefits: {
    title: "Quyền lợi học viên",
    intro: "Các quyền lợi nổi bật khi tham gia chương trình AI Thực Chiến.",
    body: benefitsPage,
  },
  schedule: {
    title: "Lịch tuyển sinh",
    intro: "Theo dõi tiến độ tuyển sinh theo từng khóa. Mỗi khóa được đào tạo trong 12 tuần.",
    body: schedulePage,
  },
  application: {
    title: "Hồ sơ & đăng ký",
    intro: "Khung thông tin cần thu thập khi học viên sẵn sàng nộp hồ sơ.",
    body: applicationPage,
  },
  career: {
    title: "Cơ hội việc làm",
    intro: "Các hướng ứng dụng sau khoá học, trình bày ở mức tư vấn định hướng.",
    body: careerPage,
  },
  posts: {
    title: "Bài viết & Hỏi đáp",
    intro: "Không gian gom bài viết giải thích chương trình và case hỏi đáp thực tế.",
    body: postsPage,
  },
  feedback: {
    title: "Phản hồi học viên",
    intro: "Góc chia sẻ trải nghiệm học tập và đóng góp giúp chương trình ngày càng thiết thực hơn.",
    body: feedbackPage,
  },
  contact: {
    title: "Liên hệ",
    intro: "Trang lấy thông tin liên hệ để chuyển cho tư vấn viên khi agent chưa đủ chắc chắn.",
    body: contactPage,
  },
};

function logo() {
  return `
    <a class="brand" href="#home" aria-label="Trang chủ">
      <img class="brand-logo" src="./assets/program-logo.jpg" alt="Vingroup" />
      <span class="brand-title">
        <strong>AI THỰC CHIẾN</strong>
        <span>CHƯƠNG TRÌNH ĐÀO TẠO NHÂN TÀI</span>
      </span>
    </a>
  `;
}

function topbar(active = "home") {
  const links = [
    ["home", "Trang chủ"],
    ["program", "Chương trình"],
    ["benefits", "Quyền lợi"],
    ["faq", "Câu hỏi thường gặp"],
    ["feedback", "Phản hồi học viên"],
    ["contact", "Liên hệ"],
  ];
  return `
    <header class="topbar">
      ${logo()}
      <button class="mobile-menu-btn" type="button" aria-label="Mở menu" aria-expanded="false">${icon("menu")}</button>
      <nav class="topnav" aria-label="Điều hướng chính">
        ${links.map(([id, label]) => `<a class="${active === id ? "active" : ""}" href="#${id}">${label}</a>`).join("")}
        <a class="primary-btn" href="#application">Đăng ký ngay</a>
      </nav>
    </header>
  `;
}

function homePage() {
  return `
    <div class="app-shell">
      ${topbar("home")}
      <main class="hero">
        <div class="hero-bg" aria-hidden="true"></div>
        <section class="hero-content">
          <p class="eyebrow">AI Tư vấn tuyển sinh</p>
          <h1>AI Tư vấn tuyển sinh <span>AI THỰC CHIẾN</span></h1>
          <p class="hero-copy">Hỏi về chương trình, điều kiện, lộ trình học và mức phù hợp. Agent trả lời dựa trên nguồn tuyển sinh đã kiểm duyệt và chuyển tư vấn viên khi thiếu căn cứ.</p>
          <form class="hero-search" data-chat-form>
            <input name="question" placeholder="Bạn muốn hỏi gì về chương trình AI Thực Chiến?" autocomplete="off" />
            <button class="send-round" type="submit" aria-label="Gửi câu hỏi">➜</button>
          </form>
          <div class="suggestions" aria-label="Gợi ý câu hỏi">
            ${[
              "Ai có thể đăng ký chương trình?",
              "Bài test đầu vào gồm những gì?",
              "Chương trình học kéo dài bao lâu?",
              "Quyền lợi của học viên là gì?",
            ].map((item) => `<button data-ask="${item}">${item}</button>`).join("")}
          </div>
        </section>
        <section class="metric-strip" aria-label="Thông tin nổi bật">
          ${[
            ["12", "Tuần đào tạo", "L"],
            ["Miễn 100%", "Học phí", "%"],
            ["8 triệu VND", "Phụ cấp / tháng", "V"],
            ["Cơ hội tuyển dụng", "Tại Vingroup", "T"],
          ].map(([value, label, icon]) => `
            <div class="metric">
              <span class="metric-icon">${icon}</span>
              <span><strong>${value}</strong><span>${label}</span></span>
            </div>
          `).join("")}
        </section>
      </main>
      <footer class="home-contact">
        <div class="home-contact-intro">
          <span class="contact-kicker">Thông tin chương trình</span>
          <h2>Đào tạo Nhân tài AI thực chiến</h2>
          <p>Đào tạo Nhân tài AI thực chiến là chương trình đặc biệt của Tập đoàn Vingroup do Trường Đại học VinUni phối hợp triển khai.</p>
        </div>
        <div class="home-contact-details">
          <p>${icon("map")}<span>VinUniversity, Vinhomes Ocean Park, Gia Lam, Hanoi, Vietnam</span></p>
          <p>${icon("phone")}<span><strong>Hotline:</strong> <a href="tel:0979489846">0979.489.846</a></span></p>
          <p>${icon("phone")}<span><strong>Liên hệ tuyển sinh:</strong> Ms. Thảo - <a href="tel:0388339478">0388.339.478</a> | Ms. Phương Anh - <a href="tel:0392509992">0392 509 992</a></span></p>
          <p>${icon("mail")}<span><strong>Email:</strong> <a href="mailto:AIthucchien@vinuni.edu.vn">AIthucchien@vinuni.edu.vn</a></span></p>
        </div>
      </footer>
    </div>
  `;
}

function dashboardShell(active, content) {
  return `
    <div class="dashboard">
      <aside class="sidebar">
        ${logo()}
        <nav class="side-nav" aria-label="Điều hướng dashboard">
          ${navItems.map((item) => `
            <a class="${active === item.id ? "active" : ""}" href="#${item.id}">
              <span class="nav-icon">${icon(item.icon)}</span><span>${item.label}</span>
            </a>
          `).join("")}
        </nav>
        <div class="side-card">
          <div class="mini-robot" aria-hidden="true"></div>
          <strong>AI TƯ VẤN TUYỂN SINH</strong>
          <p class="subtle">Chương trình AI Thực Chiến<br />Khoá cơ bản - VinUni</p>
        </div>
      </aside>
      <main class="main-area">${content}</main>
    </div>
  `;
}

function chatPage(initialQuestion = "Em học ngành Kinh tế thì có đăng ký chương trình AI Thực Chiến được không?") {
  return dashboardShell("chat", `
    <section class="chat-layout" data-live-chat data-initial-question="${escapeHtml(initialQuestion)}">
      <div class="chat-panel">
        <header class="panel-header">
          <div class="panel-title">
            <h2>AI Tư vấn tuyển sinh AI Thực Chiến</h2>
            <span class="status"><span class="dot"></span> AI đang online</span>
          </div>
          <button class="icon-btn" aria-label="Lịch sử">⋮</button>
        </header>
        <div class="messages">
          <div class="message-row user">
            <div class="bubble">${escapeHtml(initialQuestion)}<div class="subtle">10:20</div></div>
          </div>
          <div class="message-row">
            <div class="avatar">AI</div>
            <article class="bubble" data-ai-answer aria-live="polite">
              <p>Đang tra cứu nguồn tuyển sinh đã kiểm duyệt…</p>
            </article>
          </div>
        </div>
        <div class="quick-chips">
          ${[
            "Bài test đầu vào gồm những gì?",
            "Chương trình kéo dài bao lâu?",
            "Có cần biết lập trình không?",
            "Phụ cấp của chương trình là bao nhiêu?",
            "Học online hay offline?",
          ].map((item) => `<button class="chip" data-ask="${item}">${item}</button>`).join("")}
        </div>
        <form class="composer" data-chat-form>
          <input name="question" placeholder="Nhập câu hỏi của bạn..." autocomplete="off" />
          <button class="send-round" type="submit" aria-label="Gửi câu hỏi">➜</button>
        </form>
      </div>
      <aside class="resource-panel" id="source-panel" tabindex="-1">
        <h3>Nguồn tham khảo</h3>
        <div class="source-list" data-live-sources><p class="subtle">Nguồn sẽ xuất hiện sau khi agent trả lời.</p></div>
        <h3>Chủ đề phổ biến</h3>
        <div class="topic-list">
          ${topics.map((topic) => `
            <a class="topic-item" href="#faq">
              <span class="page-icon">T</span>
              <span><strong>${topic}</strong><span>Xem câu hỏi liên quan</span></span>
              <span>›</span>
            </a>
          `).join("")}
        </div>
        <a class="secondary-btn" href="#faq">Xem tất cả chủ đề</a>
      </aside>
    </section>
  `);
}

async function runChat(question) {
  const shell = document.querySelector("[data-live-chat]");
  if (!shell) return;
  const answer = shell.querySelector("[data-ai-answer]");
  const sourceList = shell.querySelector("[data-live-sources]");
  answer.innerHTML = "<p>Đang tra cứu nguồn tuyển sinh đã kiểm duyệt…</p>";
  sourceList.innerHTML = '<p class="subtle">Đang kiểm tra nguồn và độ liên quan…</p>';

  try {
    const response = await fetch(`${API_BASE}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: question,
        request_id: `web_${Date.now()}`,
        context: { session_id: sessionStorage.getItem("admission-session") || "web-demo" },
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Không thể gọi dịch vụ tư vấn");

    const validation = data.validation || {};
    const status = validation.passed
      ? `Đã kiểm chứng ${validation.evidence_count || 0} bằng chứng · relevance ${Number(validation.avg_relevance || 0).toFixed(2)} · trust ${Number(validation.avg_source_trust || 0).toFixed(2)}`
      : "Chưa đủ bằng chứng — cần tư vấn viên";
    const logs = await (await fetch(`${API_BASE}/api/logs`)).json();
    const requestLogs = logs.filter((item) => item.request_id === data.request_id);
    answer.innerHTML = `
      <p>${escapeHtml(data.response)}</p>
      <p class="subtle">${escapeHtml(status)}</p>
      <p class="subtle">Trace: ${escapeHtml(data.request_id)} · ${requestLogs.length} bước đã log · ${requestLogs.some((item) => item.step === "tool_call" && item.payload?.tool === "web.search") ? "đã gọi web search" : "local search"}</p>
      <button class="source-toggle" type="button" data-show-sources>
        Xem nguồn (${(data.sources || []).length})
      </button>
    `;
    const evidenceBySource = new Map((data.evidence || []).map((item) => [item.source_id, item]));
    const uniqueSources = [...new Map((data.sources || []).map((source) => [source.source_id, source])).values()];
    sourceList.innerHTML = uniqueSources.length
      ? uniqueSources.map((source) => `
          <div class="source-card">
            <span class="page-icon">S</span>
            <span>
              <strong>${escapeHtml(source.title)}</strong>
              <span>${escapeHtml(source.source_type)} · ${escapeHtml(evidenceBySource.get(source.source_id)?.locator || "document")} · trust ${Number(source.trust_score).toFixed(2)} · <a href="${escapeHtml(source.uri)}" target="_blank" rel="noreferrer">mở nguồn</a></span>
            </span>
          </div>
        `).join("")
      : '<p class="subtle">Không có nguồn đủ ngưỡng để trích dẫn.</p>';
    bindSourceButton();
  } catch (error) {
    answer.innerHTML = `
      <p>Agent chưa thể hoàn tất yêu cầu này.</p>
      <p class="subtle">API: ${escapeHtml(`${API_BASE || window.location.origin}/api/query`)}</p>
      <p class="subtle">Chi tiết kỹ thuật: ${escapeHtml(error.message || "Unknown error")}</p>
      <button class="source-toggle" type="button" data-retry-query>Thử lại</button>
    `;
    sourceList.innerHTML = '<p class="subtle">Chưa tải được nguồn.</p>';
    const retryButton = shell.querySelector("[data-retry-query]");
    retryButton?.addEventListener("click", () => runChat(question), { once: true });
  }
}

function bindSourceButton() {
  const sourceButton = document.querySelector("[data-show-sources]");
  if (!sourceButton || sourceButton.dataset.bound === "true") return;
  sourceButton.dataset.bound = "true";
  sourceButton.addEventListener("click", () => {
    const sourcePanel = document.getElementById("source-panel");
    if (!sourcePanel) return;
    sourcePanel.classList.remove("attention");
    requestAnimationFrame(() => sourcePanel.classList.add("attention"));
    sourcePanel.scrollIntoView({ behavior: "smooth", block: "start" });
    sourcePanel.focus({ preventScroll: true });
    sourceButton.textContent = "Đã mở danh sách nguồn";
  });
}

function contentPage(id) {
  const page = pages[id] || pages.program;
  return dashboardShell(id, `
    <section class="content-page">
      <div>
        <div class="breadcrumb">Trang chủ › ${page.title}</div>
        <div class="page-head">
          <div>
            <h1>${page.title}</h1>
            <p class="subtle">${page.intro}</p>
          </div>
          <a class="primary-btn" href="#chat">Hỏi agent</a>
        </div>
      </div>
      ${page.body()}
    </section>
  `);
}

function programPage() {
  return `
    <article class="content-card split-card">
      <div>
        <h2>Tổng quan chương trình AI Thực Chiến - Khoá Cơ bản</h2>
        <p>Chương trình đào tạo 12 tuần, kết hợp giữa nền tảng kỹ thuật, thực hành với dữ liệu và dự án cuối khoá theo bối cảnh doanh nghiệp.</p>
      </div>
      <div class="visual-tile">AI</div>
    </article>
    <section class="two-cols">
      <div class="info-tile">
        <h3>3 tuần nền tảng</h3>
        <p>Python, tư duy AI, dữ liệu cơ bản, prompt và quy trình làm sản phẩm AI.</p>
      </div>
      <div class="info-tile">
        <h3>9 tuần thực chiến</h3>
        <p>Làm việc theo nhóm, xây prototype, đo chất lượng, demo và phản biện.</p>
      </div>
    </section>
  `;
}

function admissionPage() {
  return `
    <article class="content-card split-card">
      <div>
        <h2>Điều kiện chung</h2>
        <ul class="check-list">
          <li>Tốt nghiệp đại học hoặc sắp tốt nghiệp.</li>
          <li>Mọi ngành học đều có thể đăng ký.</li>
          <li>Có tư duy logic, đam mê công nghệ và mong muốn phát triển nghề nghiệp AI.</li>
          <li>Có kinh nghiệm lập trình hoặc phân tích dữ liệu là lợi thế.</li>
          <li>Vượt qua bài kiểm tra đầu vào và vòng phỏng vấn.</li>
        </ul>
      </div>
      <div class="visual-tile">OK</div>
    </article>
    <section class="content-card">
      <h2>Yêu cầu kỹ năng khuyến nghị</h2>
      <div class="quick-chips">
        ${["Python cơ bản", "Tư duy giải quyết vấn đề", "Tiếng Anh đọc hiểu", "Làm việc nhóm"].map((item) => `<span class="chip">${item}</span>`).join("")}
      </div>
    </section>
  `;
}

function benefitsPage() {
  const benefits = [
    ["Miễn 100%", "Học phí toàn khoá"],
    ["Phụ cấp", "8 triệu VND / tháng"],
    ["Mentor 1:1", "Học cùng chuyên gia"],
    ["Dự án thực tế", "Làm bài toán doanh nghiệp"],
    ["Tuyển dụng", "Cơ hội tại hệ sinh thái Vingroup"],
    ["Cộng đồng", "Kết nối học viên chất lượng cao"],
  ];
  return `
    <section class="content-card">
      <h2>Học viên AI Thực Chiến nhận được</h2>
      <div class="benefit-grid">
        ${benefits.map(([title, desc]) => `<div class="benefit-tile"><span class="page-icon">B</span><h3>${title}</h3><p>${desc}</p></div>`).join("")}
      </div>
    </section>
    <section class="content-card">
      <h2>Bạn đã sẵn sàng trở thành nhân tài AI?</h2>
      <a class="primary-btn" href="#application">Đăng ký ngay</a>
    </section>
  `;
}

function schedulePage() {
  const steps = [
    ["Bước 1", "Mở đơn đăng ký"],
    ["Bước 2", "Xét hồ sơ trực tuyến"],
    ["Bước 3", "Đánh giá năng lực đầu vào"],
    ["Bước 4", "Thông báo kết quả"],
    ["Bước 5", "Khai giảng và đào tạo 12 tuần"],
  ];
  return `
    <section class="schedule-overview">
      <article class="current-cohort">
        <div>
          <span class="cohort-label">Khóa gần nhất</span>
          <h2>Khóa 4</h2>
          <p>Lịch nhận hồ sơ, đánh giá đầu vào và khai giảng đang được cập nhật theo thông báo chính thức của chương trình.</p>
        </div>
        <div class="duration-badge">
          <strong>12</strong>
          <span>tuần đào tạo</span>
        </div>
      </article>
      <aside class="schedule-note">
        ${icon("calendar")}
        <div>
          <strong>Lịch có thể được điều chỉnh</strong>
          <p>Các mốc tuyển sinh không cố định giữa các khóa. Ứng viên nên kiểm tra thông báo mới nhất hoặc liên hệ đội ngũ tuyển sinh trước khi chuẩn bị hồ sơ.</p>
        </div>
      </aside>
    </section>
    <section class="content-card schedule-card">
      <div class="schedule-section-head">
        <div>
          <span class="contact-kicker">Quy trình dự kiến</span>
          <h2>Các bước của một đợt tuyển sinh</h2>
        </div>
        <a class="secondary-btn" href="#contact">Kiểm tra lịch mới nhất</a>
      </div>
      <div class="timeline">
        ${steps.map(([stage, label], index) => `
          <div class="timeline-item">
            <span class="timeline-dot">${index + 1}</span>
            <div><strong>${label}</strong><p class="subtle">${stage} · Thời gian sẽ được thông báo</p></div>
          </div>
        `).join("")}
      </div>
      <a class="primary-btn" href="#application">Đăng ký quan tâm</a>
    </section>
    <section class="content-card cohort-history">
      <div>
        <span class="contact-kicker">Các khóa đã công bố</span>
        <h2>Chương trình hiện hiển thị đến Khóa 4</h2>
      </div>
      <div class="cohort-list">
        ${[1, 2, 3, 4].map((cohort) => `
          <div class="cohort-item ${cohort === 4 ? "active" : ""}">
            <span>Khóa ${cohort}</span>
            <strong>${cohort === 4 ? "Khóa gần nhất" : "Khóa trước"}</strong>
          </div>
        `).join("")}
      </div>
    </section>
  `;
}

function applicationPage() {
  return `
    <section class="contact-grid">
      <form class="content-card form" data-application-form>
        <h2>Thông tin đăng ký</h2>
        <input name="fullName" placeholder="Họ và tên" required />
        <input name="email" type="email" placeholder="Email" required />
        <input name="phone" type="tel" placeholder="Số điện thoại" required />
        <select name="goal" required>
          <option value="">Mục tiêu học tập</option>
          <option>Chuyển ngành sang AI</option>
          <option>Ứng dụng AI trong công việc</option>
          <option>Nâng cấp năng lực kỹ thuật</option>
        </select>
        <textarea name="question" placeholder="Bạn muốn agent tư vấn thêm điều gì?"></textarea>
        <label class="upload-box" for="cv-upload">
          ${icon("upload", "upload-icon")}
          <span>
            <strong>Nộp CV của bạn</strong>
            <small data-file-name>Chọn tệp PDF hoặc DOCX, tối đa 10 MB</small>
          </span>
          <span class="secondary-btn">Chọn tệp</span>
        </label>
        <input class="visually-hidden" id="cv-upload" name="cv" type="file" accept=".pdf,.doc,.docx" />
        <p class="form-error" data-application-error role="alert"></p>
        <button class="primary-btn" type="submit">Gửi hồ sơ</button>
      </form>
      <div class="application-guide">
        <article class="content-card guide-card">
          <span class="guide-icon">${icon("file")}</span>
          <h2>Hướng dẫn nộp CV</h2>
          <ol class="step-list">
            <li><span>1</span><div><strong>Định dạng rõ ràng</strong><p>Ưu tiên PDF, tên tệp theo mẫu HoTen_CV.pdf.</p></div></li>
            <li><span>2</span><div><strong>Nêu bật nền tảng phù hợp</strong><p>Trình bày học vấn, kỹ năng kỹ thuật, dự án và kinh nghiệm liên quan.</p></div></li>
            <li><span>3</span><div><strong>Kiểm tra trước khi gửi</strong><p>Đảm bảo email, số điện thoại và đường dẫn portfolio còn hoạt động.</p></div></li>
          </ol>
        </article>
        <article class="content-card compact-card">
          <h3>Checklist hồ sơ</h3>
          <ul class="check-list">
            <li>CV và thông tin nền tảng học thuật - kỹ thuật.</li>
            <li>Portfolio hoặc hồ sơ năng lực nếu có.</li>
            <li>Mục tiêu tham gia chương trình.</li>
          </ul>
        </article>
      </div>
    </section>
  `;
}

function careerPage() {
  return `
    <section class="job-grid">
      ${[
        ["AI Product Assistant", "Hỗ trợ phân tích nhu cầu và thiết kế tính năng AI."],
        ["Data Analyst", "Khai thác dữ liệu, xây dashboard, đánh giá kết quả thử nghiệm."],
        ["Automation Builder", "Tự động hoá quy trình nội bộ bằng công cụ AI."],
      ].map(([title, desc]) => `<article class="job-tile"><h3>${title}</h3><p>${desc}</p></article>`).join("")}
    </section>
  `;
}

function faqPage() {
  const faqs = [
    ["Ngành không kỹ thuật có đăng ký được không?", "Có, nếu ứng viên có tư duy logic, động lực rõ ràng và sẵn sàng bổ sung nền tảng."],
    ["Có cần biết lập trình trước không?", "Không bắt buộc ở mức nâng cao, nhưng Python cơ bản là lợi thế lớn."],
    ["Agent có cam kết trúng tuyển không?", "Không. Agent chỉ tư vấn mức phù hợp và các bước chuẩn bị dựa trên nguồn tham khảo."],
    ["Khi nào cần chuyển tư vấn viên?", "Khi câu hỏi liên quan chính sách cá nhân, học phí cụ thể, cam kết hoặc thông tin chưa có trong nguồn."],
  ];
  return `
    <section class="faq-grid">
      ${faqs.map(([q, a]) => `<article class="faq-item"><h3>${q}</h3><p>${a}</p></article>`).join("")}
    </section>
  `;
}

function postsPage() {
  return `
    <section class="two-cols">
      ${[
        ["Cách tự đánh giá mức phù hợp với khoá AI", "Bài viết hướng dẫn ứng viên chuẩn bị trước khi trò chuyện với agent."],
        ["Những câu hỏi nên hỏi trước khi đăng ký", "Danh sách câu hỏi giúp tránh kỳ vọng sai về chương trình."],
        ["Từ trái ngành sang AI cần chuẩn bị gì?", "Gợi ý lộ trình nền tảng cho người chưa có kinh nghiệm kỹ thuật."],
        ["Agent tuyển sinh nên biết khi nào không biết", "Nguyên tắc an toàn để không tư vấn quá thẩm quyền."],
      ].map(([title, desc]) => `<article class="info-tile"><h3>${title}</h3><p>${desc}</p><a href="#chat">Hỏi thêm ›</a></article>`).join("")}
    </section>
  `;
}

function feedbackPage() {
  const feedbacks = [
    ["N.T. Minh", "Học viên khối Kỹ thuật", "Phần dự án giúp mình hiểu rõ cách đưa một ý tưởng AI thành sản phẩm có thể trình diễn và đánh giá."],
    ["L.H. Trang", "Học viên chuyển ngành", "Mentor phản hồi rất sát vấn đề. Mình tiến bộ nhanh nhất ở cách chia nhỏ bài toán và kiểm chứng kết quả."],
    ["P.Q. Nam", "Học viên khối Kinh doanh", "Chương trình giúp mình kết nối kiến thức nghiệp vụ với công cụ AI trong một quy trình làm việc thực tế."],
  ];
  return `
    <section class="feedback-summary">
      <div><strong>4.9</strong><span>${icon("star")} ${icon("star")} ${icon("star")} ${icon("star")} ${icon("star")}</span><small>Điểm hài lòng minh họa</small></div>
      <p>Các nội dung bên dưới là dữ liệu mẫu cho giao diện. Khi kết nối backend, trang có thể hiển thị phản hồi đã được chương trình xác minh.</p>
    </section>
    <section class="feedback-grid">
      ${feedbacks.map(([name, role, quote]) => `
        <article class="feedback-card">
          <div class="quote-mark">“</div>
          <p>${quote}</p>
          <div class="feedback-author"><span>${name.split(".").join("").slice(0, 2)}</span><div><strong>${name}</strong><small>${role}</small></div></div>
        </article>
      `).join("")}
    </section>
    <form class="content-card feedback-form" data-demo-form data-success-message="Phản hồi đã được ghi nhận trong bản demo và đang chờ kiểm duyệt.">
      <div>
        <span class="contact-kicker">Chia sẻ trải nghiệm</span>
        <h2>Gửi phản hồi của bạn</h2>
        <p class="subtle">Phản hồi sẽ được kiểm duyệt trước khi hiển thị công khai.</p>
      </div>
      <div class="rating-control" aria-label="Chọn mức đánh giá">
        ${[1, 2, 3, 4, 5].map((value) => `<button type="button" data-rating="${value}" aria-label="${value} sao">${icon("star")}</button>`).join("")}
      </div>
      <input name="fullName" placeholder="Họ và tên" required />
      <input name="role" placeholder="Khóa học / vai trò" required />
      <textarea name="feedback" placeholder="Chia sẻ điều bạn thấy hữu ích hoặc mong muốn chương trình cải thiện..." required></textarea>
      <button class="primary-btn" type="submit">Gửi phản hồi</button>
    </form>
  `;
}

function contactPage() {
  return `
    <section class="contact-grid">
      <article class="content-card contact-card">
        <span class="contact-kicker">Kênh tuyển sinh chính thức</span>
        <h2>Liên hệ chương trình</h2>
        <p class="contact-description">Đào tạo Nhân tài AI thực chiến là chương trình đặc biệt của Tập đoàn Vingroup do Trường Đại học VinUni phối hợp triển khai.</p>
        <div class="contact-list">
          <p>${icon("map")}<span>VinUniversity, Vinhomes Ocean Park, Gia Lam, Hanoi, Vietnam</span></p>
          <p>${icon("phone")}<span><strong>Hotline</strong><a href="tel:0979489846">0979.489.846</a></span></p>
          <p>${icon("phone")}<span><strong>Ms. Thảo</strong><a href="tel:0388339478">0388.339.478</a></span></p>
          <p>${icon("phone")}<span><strong>Ms. Phương Anh</strong><a href="tel:0392509992">0392 509 992</a></span></p>
          <p>${icon("mail")}<span><strong>Email</strong><a href="mailto:AIthucchien@vinuni.edu.vn">AIthucchien@vinuni.edu.vn</a></span></p>
        </div>
      </article>
      <form class="content-card form" data-demo-form data-success-message="Yêu cầu gọi lại đã được ghi nhận trong bản demo.">
        <h2>Yêu cầu tư vấn viên gọi lại</h2>
        <input name="fullName" placeholder="Họ và tên" required />
        <input name="phone" type="tel" placeholder="Số điện thoại" required />
        <textarea name="request" placeholder="Nội dung cần tư vấn" required></textarea>
        <button class="primary-btn" type="submit">Gửi yêu cầu</button>
      </form>
    </section>
  `;
}

function render() {
  const hash = window.location.hash.replace("#", "") || "home";
  const storedQuestion = sessionStorage.getItem("admission-question");

  if (hash === "home") {
    document.getElementById("app").innerHTML = homePage();
  } else if (hash === "chat") {
    document.getElementById("app").innerHTML = chatPage(storedQuestion || undefined);
  } else {
    document.getElementById("app").innerHTML = contentPage(hash);
  }

  bindInteractions();
  const liveChat = document.querySelector("[data-live-chat]");
  if (liveChat) {
    runChat(liveChat.dataset.initialQuestion);
  }
}

function bindInteractions() {
  document.querySelectorAll("[data-chat-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const question = new FormData(form).get("question");
      if (question && String(question).trim()) {
        sessionStorage.setItem("admission-question", String(question).trim());
      }
      if (window.location.hash === "#chat") {
        render();
      } else {
        window.location.hash = "chat";
      }
    });
  });

  document.querySelectorAll("[data-ask]").forEach((button) => {
    button.addEventListener("click", () => {
      sessionStorage.setItem("admission-question", button.dataset.ask);
      window.location.hash = "chat";
    });
  });

  const upload = document.getElementById("cv-upload");
  if (upload) {
    upload.addEventListener("change", () => {
      const label = document.querySelector("[data-file-name]");
      const uploadBox = document.querySelector(".upload-box");
      const error = document.querySelector("[data-application-error]");
      if (label && upload.files.length) {
        label.textContent = upload.files[0].name;
      }
      uploadBox?.classList.remove("invalid");
      if (error) error.textContent = "";
    });
  }

  const applicationForm = document.querySelector("[data-application-form]");
  if (applicationForm) {
    applicationForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const error = applicationForm.querySelector("[data-application-error]");
      const uploadBox = applicationForm.querySelector(".upload-box");
      const file = upload?.files?.[0];

      if (!file) {
        if (error) error.textContent = "Vui lòng chọn CV trước khi gửi hồ sơ.";
        uploadBox?.classList.add("invalid");
        uploadBox?.scrollIntoView({ behavior: "smooth", block: "center" });
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        if (error) error.textContent = "CV vượt quá dung lượng tối đa 10 MB.";
        uploadBox?.classList.add("invalid");
        return;
      }

      applicationForm.innerHTML = `
        <div class="completion-state">
          <span class="completion-icon">${icon("check")}</span>
          <span class="contact-kicker">Hoàn tất flow CP2</span>
          <h2>Đã hoàn tất bước nộp hồ sơ</h2>
          <p>Thông tin và tệp <strong>${escapeHtml(file.name)}</strong> đã được ghi nhận trong phiên demo.</p>
          <div class="prototype-note">Đây là bản prototype. Dữ liệu chưa được gửi tới hệ thống tuyển sinh VinUni.</div>
          <div class="completion-actions">
            <a class="primary-btn" href="#chat">Tiếp tục hỏi agent</a>
            <a class="secondary-btn" href="#home">Về trang chủ</a>
          </div>
        </div>
      `;
    });
  }

  document.querySelectorAll("[data-demo-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      let notice = form.querySelector(".form-notice");
      if (!notice) {
        notice = document.createElement("div");
        notice.className = "form-notice";
        notice.setAttribute("role", "status");
        form.appendChild(notice);
      }
      notice.innerHTML = `${icon("check")}<span>${escapeHtml(form.dataset.successMessage)}</span>`;
      form.reset();
      form.querySelectorAll("[data-rating]").forEach((item) => item.classList.remove("selected"));
      notice.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  });

  bindSourceButton();

  document.querySelectorAll("[data-rating]").forEach((button) => {
    button.addEventListener("click", () => {
      const selected = Number(button.dataset.rating);
      document.querySelectorAll("[data-rating]").forEach((item) => {
        item.classList.toggle("selected", Number(item.dataset.rating) <= selected);
      });
    });
  });

  const menuButton = document.querySelector(".mobile-menu-btn");
  if (menuButton) {
    menuButton.addEventListener("click", () => {
      const topbar = menuButton.closest(".topbar");
      const isOpen = topbar.classList.toggle("menu-open");
      menuButton.setAttribute("aria-expanded", String(isOpen));
      menuButton.setAttribute("aria-label", isOpen ? "Đóng menu" : "Mở menu");
    });
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

window.addEventListener("hashchange", render);
render();
