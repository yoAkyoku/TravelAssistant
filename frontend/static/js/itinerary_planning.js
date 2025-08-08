// 切換面板內容
function switchTab(index) {
    // Remove 'active' class from all tabs and add to the selected one
    document.querySelectorAll(".tab").forEach((tab, i) => {
        tab.classList.toggle("active", i === index);
    });
    // Hide all tab contents and show the selected one
    document.querySelectorAll(".tab-content").forEach((tabContent, i) => {
        tabContent.style.display = i === index ? "block" : "none";
    });
}

// 摺疊行程細節
function toggleDetails(card) {
    const detail = card.querySelector(".itinerary-details");
    // Toggle display between 'block' and 'none'
    if (detail.style.display === "none" || detail.style.display === "") {
        detail.style.display = "block";
    } else {
        detail.style.display = "none";
    }
}

// Resizer functionality
const resizer = document.getElementById('resizer');
const chat = document.getElementById('chat-section');
const itinerary_panel = document.getElementById('itinerary-panel');
let isResizing = false;

// 監視滑鼠按下事件
resizer.addEventListener('mousedown', (e) => {
    isResizing = true;
    // Change cursor to indicate resizing
    document.body.style.cursor = 'col-resize';
});

// 監視滑鼠移動事件 (縮放分隔線)
window.addEventListener('mousemove', (e) => {
    if (!isResizing) return;

    const container = document.getElementById('container');
    const containerWidth = container.clientWidth;
    const containerOffsetLeft = container.offsetLeft;
    const pointerRelativeXpos = e.clientX - containerOffsetLeft;

    const minWidth = 300;
    const maxWidth = containerWidth - minWidth;

    if (pointerRelativeXpos > minWidth && pointerRelativeXpos < maxWidth) {
        const chatPercent = (pointerRelativeXpos / containerWidth) * 100;
        const sidebarPercent = 100 - chatPercent;

        chat.style.width = `${chatPercent}%`;
        itinerary_panel.style.width = `${sidebarPercent}%`;
    }
});

// 監視滑鼠放開事件
window.addEventListener('mouseup', () => {
    isResizing = false;
    // Restore default cursor
    document.body.style.cursor = 'default';
});

// 監視訊息送出事件
document.getElementById("send-btn").addEventListener("click", sendMessage);
document.getElementById("user-input").addEventListener("keypress", function (e) {
    if (e.key === "Enter") sendMessage();
});

// 用戶發送訊息 (聊天)
async function sendMessage() {
    const inputEl = document.getElementById("user-input");
    const message = inputEl.value.trim();
    if (!message) return;

    // 顯示使用者訊息
    appendMessage("user", message);
    inputEl.value = "";

    const requestData = {
        "user_id": "1",
        "plan_id": "1",
        "message": message
    };

    startNewAIMessage();

    try {
        const response = await fetch("http://localhost:8000/api/travel/chat/stream", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const contentType = response.headers.get("content-type");
            const errorBody = await contentType.includes("application/json")?response.json():response.text(); // 嘗試解析JSON，否則獲取文本
            const errorMessage = errorBody.detail || errorBody || "未知錯誤";
            throw new Error(`API 請求失敗: ${response.status} ${response.statusText} - ${errorMessage}`);
        }
        
        // 處理ReadableStream (Fetch API的串流響應)
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8"); // 用於解碼bytes到string

        let aiBuffer = "";
        let buffer = ""; // 用於緩衝SSE數據，因為數據可能分塊到達

        if (currentTypingEl) {
            currentTypingEl.classList.add("glow");
        }

        while (true) {
            const { value, done } = await reader.read(); // 讀取數據塊
            if (done) {
                console.log("🔗 SSE stream finished from fetch.");
                break; // 串流結束
            }

            // 將接收到的 bytes 轉換為字符串並追加到緩衝區
            buffer += decoder.decode(value, { stream: true });

            // 處理可能包含多個或不完整事件的緩衝區
            // SSE事件以\n\n分隔
            const events = buffer.split('\n\n');
            buffer = events.pop(); // 保留最後一個可能不完整的事件在緩衝區

            for (const eventString of events) {
                if (!eventString.startsWith("data: ")) continue; // 忽略非數據行

                const jsonString = eventString.substring(6); // 移除 "data: "
                if (jsonString === "[DONE]") {
                    console.log("✅ Stream [DONE] received.");
                    reader.releaseLock(); // 釋放讀取器鎖
                    if (currentTypingEl) currentTypingEl.classList.remove("glow");
                    return; // 結束函數
                }

                try {
                    const data = JSON.parse(jsonString);
                    // console.log("🟡 Received data:", data);
                    
                    if (data.status) {
                        await updateTypingAIMessage(data.status, true); // 顯示工具進度或提示
                    }

                    if (data.node === "generate_itinerary" || data.node === "modify_plan") {
                        showItineraryLoading(); // 生成/修改行程時載入讀取動畫
                    }
                    
                    if (data.message?.type === "ai") {
                        if (data.node === "collect_preferences" || data.node === "modify_plan") {
                            isStatusMessage = true;
                            await updateTypingAIMessage(data.message.content, true); // 回復用戶的狀態訊息
                        }else {
                            await updateTypingAIMessage(data.message.content, false); // 持續更新訊息內容
                        }
                    }

                    if (data.itinerary) {
                        hideItineraryLoading();
                        renderItineraryTab(JSON.parse(data.itinerary)); // 更新右側行程卡片
                    }

                    // 如果有錯誤從後端串流過來
                    if (data.error) {
                        msg = `⚠️ 後端錯誤：${data.error}`;
                        typeWriter(msg);
                        reader.releaseLock(); // 釋放讀取器鎖
                        return; // 結束函數
                    }

                } catch (parseErr) {
                    console.error("❌ JSON parse error for event:", parseErr, "Event string:", jsonString);
                    // 可以選擇向用戶顯示解析錯誤
                }
            }
        }
    } catch (err) {
        console.error("❌ Error in sendMessage:", err);
        msg = "⚠️ 系統錯誤，請稍後再試。";
        typeWriter(msg);
    }
}

// 添加訊息至對話框
function appendMessage(sender, content) {
    const box = document.getElementById("chat-box");
    const msg = document.createElement("div");
    msg.className = `chat-message ${sender}-message`;
    msg.innerText = content;
    box.appendChild(msg);
    autoScrollChatBox();
}

let currentTypingEl = null;
let lastAIContent = "";
let isStatusMessage = false;
let inHtmlBlock = false;
const elementStack = [];  // 用於維護 HTML tag 結構

// 空的AI訊息元素並將其添加到聊天視窗中
function startNewAIMessage() {
    const box = document.getElementById("chat-box");
    currentTypingEl = document.createElement("div");
    currentTypingEl.classList.add("chat-message")
    currentTypingEl.classList.add("ai-message");
    currentTypingEl.style.display = "none";
    currentTypingEl.innerHTML = "";  // 開始是空的
    elementStack.push(currentTypingEl);

    box.appendChild(currentTypingEl);
    autoScrollChatBox();

    lastAIContent = "";
    isStatusMessage = false;
    inHtmlBlock = false;
}

// 更新的AI訊息 (stream response)
async function updateTypingAIMessage(content, bOverride) {
    if (!currentTypingEl) return;
    if (currentTypingEl.style.display === "none") {
        currentTypingEl.style.display = "block";
    }

    if (bOverride) {
        // 顯示狀態（例如：正在搜尋...)
        currentTypingEl.innerHTML = "";
        typeWriter(content);
        isStatusMessage = true;
        lastAIContent = "";
        inHtmlBlock = false;
        return;
    }
    
    if (isStatusMessage) {
        currentTypingEl.innerHTML = "";
        isStatusMessage = false;
    }
    
    await processContentChunk(content);
}

// 專門解析 tag 與文字並 append 的函式
function appendToTypingEl(token) {
    const top = elementStack[elementStack.length - 1];
    top.innerHTML += token;
    autoScrollChatBox();
}

// 將 HTML 字串斷詞成 tag 與文字
function tokenizeHTML(str) {
    const regex = /(<\/?[a-zA-Z][^>]*?>)|([^<]+)/gs;
    const tokens = [];
    let match;
    while ((match = regex.exec(str)) !== null) {
        if (match[1]) tokens.push(match[1]);     // HTML tag
        if (match[2]) tokens.push(match[2]);     // Text
    }
    return tokens;
}

async function processContentChunk(content) {
    lastAIContent += content;

    // 嘗試抓取完整的 markdown html 區塊
    const htmlBlockRegex = /```html\s*([\s\S]*?)\s*```/m;
    const htmlMatch = lastAIContent.match(htmlBlockRegex);

    if (htmlMatch) {
        // 1. 有完整 html 區塊，先處理前面的純文字
        const beforeHtml = lastAIContent.slice(0, htmlMatch.index);
        if (beforeHtml.trim()) {
            await typeWriter(beforeHtml);
        }

        // 2. 處理 html 區塊
        const html = htmlMatch[1].trim();
        appendToTypingEl(html);

        // 3. 處理 html 區塊後面的內容（可能還有下一個區塊或純文字）
        lastAIContent = lastAIContent.slice(htmlMatch.index + htmlMatch[0].length);
        if (lastAIContent.length > 0) {
            processContentChunk(""); // 遞迴處理剩下的內容
        } else {
            lastAIContent = "";
        }
    } else {
        // 沒有完整 html 區塊，先不動，等 chunk 累積到完整再處理
        // 但如果你想讓純文字即時顯示，可以這樣：
        // 只要沒遇到 ```html 就直接 append
        const htmlStart = lastAIContent.indexOf("```html");
        if (htmlStart === -1 && lastAIContent.trim() && lastAIContent.length > 4) {
            await typeWriter(lastAIContent);
            lastAIContent = "";
        }
    }
}

function typeWriter(content) {
    return new Promise(resolve => {
        const chars = content.split("");
        let i = 0;

        function typeNextChar() {
            if (i < chars.length) {
                appendToTypingEl(chars[i]);
                i++;
                setTimeout(typeNextChar, 50); // 每 50ms 打一個字
            } else {
                resolve(); // 所有字都打完了，解析 Promise
            }
        }

        if (chars.length > 0) {
            typeNextChar(); // 開始打字
        } else {
            resolve(); // 如果內容為空，立即解析
        }
    });

}

// 自動滾動
function autoScrollChatBox() {
    // 判斷使用者是否接近底部
    const chatBox = document.getElementById("chat-box");
    const isScrolledToBottom = chatBox.scrollHeight - chatBox.clientHeight <= chatBox.scrollTop + 100;

    // 如果使用者已經在底部附近，或者聊天框內容剛開始生成，則自動滾動
    if (isScrolledToBottom) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    // 如果使用者手動滾動到上方，就不做任何操作，讓使用者可以繼續閱讀舊內容
}

function showItineraryLoading() {
    const tab0 = document.getElementById("tab-0");
    tab0.classList.add("loading");
    document.getElementById("itinerary-placeholder").classList.add("loading");
    document.getElementById("itinerary-placeholder").style.display = "block";
    document.getElementById("itinerary-content").style.display = "none";
}

function hideItineraryLoading() {
    const tab0 = document.getElementById("tab-0");
    tab0.classList.remove("loading");
    document.getElementById("itinerary-placeholder").classList.remove("loading");
    document.getElementById("itinerary-placeholder").style.display = "none";    
}

let currentItinerary = null

// 更新行程面板資訊
function renderItineraryTab(itinerary) {
    const contentBox = document.getElementById('itinerary-content');
    if (!contentBox || !itinerary.days) return;
    contentBox.style.display = "block";
    currentItinerary = itinerary;
    console.log(currentItinerary);
    const summaryHTML = `
        <div><strong>出發地:</strong> ${itinerary.departure_location}</div>
        <div><strong>目的地:</strong> ${itinerary.destination}</div>
        <div><strong>出發日:</strong> ${itinerary.start_date}</div>
        <div><strong>天數:</strong> ${itinerary.duration}</div>
        <div><strong>旅遊特色:</strong> ${itinerary.features}</div>
        <hr>
    `;

    const daysHTML = itinerary.days.map((day, i) => {
        const activitiesHTML = day.segments.map(segment => {
            const acts = segment.activities.map(act => `
                <br>
                <div><strong>活動:</strong> ${act.activity_name}</div>
                <div><strong>位置:</strong> ${act.activity_location}</div>
                <div><strong>類型:</strong> ${act.type}</div>
                <div><strong>內容:</strong> ${act.description}</div>
                <div><strong>備註:</strong> ${act.notes || '無'}</div>
                <br>
            `).join("");
            return `
                <div><strong>${segment.time_slot}:</strong></div>
                ${acts}
            `;
        }).join("");

        const accommodationHTML = day.accommodation? `
            <div><strong>住宿:</strong> ${day.accommodation.name?? '未提供'}</div>
            <div><strong>地址:</strong> ${day.accommodation.address?? '未提供'}</div>
        `: '<div><strong>住宿:</strong> 無</div><br>'

        return `
            <div class="itinerary-card" onclick="toggleDetails(this)">
                Day ${i + 1} - ${day.daily_theme}
                <div class="itinerary-details">
                    ${accommodationHTML}
                    ${activitiesHTML}
                </div>
            </div>
        `;
    }).join("");

    contentBox.innerHTML = summaryHTML + daysHTML;
}

async function savePlan(planId) {
    if (!planId) {
        alert("計畫 ID 無效，無法儲存。");
        return;
    }

    if (!confirm("確定要將計畫狀態標記為 '已計畫' 並儲存嗎？")) {
        return;
    }
    
    currentItinerary["status"] = 'planned'
    console.log(currentItinerary);

    try {
        const response = await fetch(`/travel_plan/plans/${planId}/status`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(currentItinerary)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: '未知錯誤' }));
            throw new Error(errorData.message || `更新計畫狀態失敗 (HTTP 狀態碼: ${response.status})`);
        }

        const result = await response.json();
        alert("計畫狀態更新成功！");
        console.log("更新後的計畫:", result);
    } catch (error) {
        console.error("儲存計畫時發生錯誤:", error);
        alert(`儲存計畫失敗: ${error.message || '請稍後再試。'}`);
    }
}