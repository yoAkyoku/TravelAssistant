document.addEventListener('DOMContentLoaded', (e) => {
    async function loadPlans() {
        const planContainer = document.getElementById('planContainer');
        if (!planContainer) return;

        el = document.querySelector('.no-plans-message');
        el.style.display = 'block';
        el.innerText = '載入旅遊計畫中...';

        try {
            const response = await fetch('/travel_plan/plans'); 
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: '未知錯誤' }));
                throw new Error(errorData.message || `載入計畫列表失敗 (HTTP 狀態碼: ${response.status})`);
            }

            const res = await response.json();
            planContainer.innerHTML = ''; 
            plans = res.status === "success"? res.plans:null;

            if (plans && plans.length > 0) {
                console.log(plans);
                el.style.display = 'none';
                // 遍歷所有計畫並為每個計畫創建 HTML 卡片
                plans.forEach(plan => {
                    console.log(plan);
                    const planCard = document.createElement('div');
                    planCard.className = 'plan-card'; // 應用 CSS 樣式
                    // 為滑鼠事件添加監聽器，而非直接寫在 HTML 屬性中，更符合 JS 最佳實踐
                    planCard.addEventListener('mouseenter', () => showActions(planCard));
                    planCard.addEventListener('mouseleave', () => hideActions(planCard));
                    
                    const travelTheme = plan.travel_theme || '無主題';
                    const lastUpdated = plan.updated_at ? new Date(plan.updated_at).toLocaleString() : new Date(plan.created_at).toLocaleString();
                    const imageUrl = "";

                    planCard.innerHTML = `
                        <a href="/travel_plan/plans/${plan.id}" class="card-link">
                            <div class="card-content-wrapper">
                                <div class="card-background" style="background-image: url('${imageUrl}');">
                                </div>
                            </div>
                            <div class="card-details">
                                <h2>${travelTheme}</h2>
                                <p class="card-updated">上次更新：${lastUpdated}</p>
                            </div>
                            <div class="floating-actions">
                                <button onclick="editPlan(event, ${plan.id})" style="color: aqua;">Edit<i class="bi bi-pencil-square"></i></button>
                                <button onclick="deletePlan(event, ${plan.id})" style="color: red;">Delete<i class="bi bi-trash"></i></button>
                            </div>
                        </a>
                    `;
                    planContainer.appendChild(planCard);
                });
            } else {
                setTimeout(() => { // 延遲1s，提升觀感
                    el.style.display = 'block';
                    el.innerText = '目前尚無旅遊規劃。';
                }, 500);
            }
        } catch (error) {
            setTimeout(() => {
                el.style.display = 'block';
                el.style.color = 'red';
                el.innerText = `載入旅遊計畫失敗: ${error.message}` || '請稍後再試。';
            }, 500);
        }
    }

    function createPlan() {
        const planData = {
            travel_theme: "我的新旅遊計畫- ",
        };

        fetch('/travel_plan/plans', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(planData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.message || '無法創建計畫'); });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // alert('計畫創建成功！計畫 ID: ' + data.plan_id);
                // 創建成功後，可以選擇重新導向到新計畫的詳情頁
                console.log(data);
                window.location.href = '/travel_plan/plans/' + data.plan_id;
            } else {
                alert('創建失敗: ' + data.message);
            }
        })
        .catch(error => {
            console.error('創建計畫時發生錯誤:', error);
            alert('創建計畫失敗: ' + error.message);
        });
    }

    function editPlan(e, planId) {
        e.stopPropagation();
        e.preventDefault();
    //     fetch(`/travel_plan/plans/${planId}`)
    //     .then(response => {
    //         if (!response.ok) {
    //             return response.json().then(err => {
    //                 throw new Error(err.message || `無法獲取計畫 ID: ${planId} 的詳細資料`);
    //             });
    //         }
    //         return response.json();
    //     })
    //     .then(planData => {
    //         console.log('獲取到的計畫資料:', planData);
    //         // 更新計畫UI
    //     })
    //     .catch(error => {
    //         console.error('獲取計畫資料時發生錯誤:', error);
    //         alert('載入編輯資料失敗: ' + error.message);
    //     });
    }

    function deletePlan(e, planId) {
        e.stopPropagation();
        e.preventDefault();
        if (confirm("確定要刪除這個規劃嗎？")) {
            fetch(`/travel_plan/plans/${planId}`, { method: 'DELETE' })
                .then(res => {
                    if (res.ok) {
                        const planCardToRemove = e.target.closest('.plan-card');
                        if (planCardToRemove) {
                            planCardToRemove.remove(); // 從 DOM 中移除該元素
                        }

                        // 檢查是否所有計畫都被刪除了，然後顯示「目前尚無旅遊規劃」訊息
                        const planContainer = document.getElementById('planContainer');
                        const el = document.querySelector('.no-plans-message');
                        if (planContainer && planContainer.children.length === 0) {
                            el.style.display = 'block';
                            el.innerText = '目前尚無旅遊規劃。';
                        }
                    } else {
                        alert("刪除失敗"); // 失敗則提示
                    }
                })
                .catch(error => { // 增加錯誤處理
                    alert("刪除時發生錯誤，請稍後再試。");
                });
        }
    }

    function showActions(card) {
        const actions = card.querySelector('.floating-actions'); // 找到卡片內的浮動操作按鈕區域
        const bg = card.querySelector('.card-background'); // 找到卡片背景圖區域
        if (actions) actions.style.display = 'flex'; // 如果找到按鈕區域，就將其顯示為 flex 佈局
        if (bg) bg.classList.add('blurred'); // 如果找到背景圖區域，就為其添加 'blurred' 類別，使其模糊
    }

    function hideActions(card) {
        const actions = card.querySelector('.floating-actions');
        const bg = card.querySelector('.card-background');
        if (actions) actions.style.display = 'none'; // 隱藏浮動操作按鈕區域
        if (bg) bg.classList.remove('blurred'); // 移除 'blurred' 類別，取消背景圖模糊
    }

    loadPlans();
    window.createPlan = createPlan;
    window.editPlan = editPlan;
    window.deletePlan = deletePlan;
    window.showActions = showActions;
    window.hideActions = hideActions;
})