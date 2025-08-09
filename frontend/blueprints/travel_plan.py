from flask import Blueprint, render_template, request, jsonify, abort
import requests
import json

plan_bp = Blueprint("travel_plan", __name__, url_prefix="/travel_plan")

FASTAPI_BASE_URL = "http://backend:8000/api/travel"

@plan_bp.route("/")
def travel_plan_page():
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/plans")
        response.raise_for_status() # 檢查 HTTP 請求是否成功
        plans = response.json()
        return render_template("travel_plan.html", plans=plans, user=None)
    except requests.exceptions.RequestException as e:
            return jsonify({"status": "error", "message": f"無法連接後端服務: {e}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@plan_bp.route("/plans", methods=["POST"])
def new_plan():
    try: 
        data = request.get_json()
        print(data)
        if not data:
            return jsonify({"status": "error", "message": "請求體不能為空"}), 400
        response = requests.post(f"{FASTAPI_BASE_URL}/plans", json=data)
        response.raise_for_status()
        created_plan = response.json()
        return jsonify({"status": "success", "plan_id": created_plan.get("id")}), 201
    
    except requests.exceptions.HTTPError as e:
        error_detail = "未知錯誤"
        try:
             error_detail = e.response.json().get("detail", "沒有詳細錯誤信息")
        except json.JSONDecodeError:
            # 如果响应不是 JSON 格式
            error_message += f" - 響應體不是有效的 JSON，內容: {e.response.text[:200]}..." # 打印部分响应体
        except Exception as inner_e:
            # 捕获其他解析或处理异常
            error_message += f" - 解析錯誤時發生未知錯誤: {inner_e}"
        return jsonify({"status": "error", "message": f"後端請求失敗: {error_detail}"}), e.response.status_code
    except requests.exceptions.ConnectionError as e: # 捕獲連線特定的錯誤
        return jsonify({"status": "error", "message": f"無法連接後端服務: {e}"}), 503 # 使用 503 Service Unavailable
    except requests.exceptions.RequestException as e: # 捕獲其他請求相關的錯誤
        return jsonify({"status": "error", "message": f"請求失敗: {e}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# @plan_bp.route("/plans/<int:plan_id>/", methods=["PUT"])
# def update_plan(plan_id):
#     try:
#         data = request.get_json()
        
#         # 由於 Pydantic 模型對日期格式有要求，如果從前端接收的日期是字串，需要轉換
#         # 這裡假設前端傳過來的日期已經是 "YYYY-MM-DD" 格式
#         if 'start_date' in data and data['start_date']:
#             data['start_date'] = datetime.strptime(data['start_date'], '%Y-%m-%d').date().isoformat()
#         if 'end_date' in data and data['end_date']:
#             data['end_date'] = datetime.strptime(data['end_date'], '%Y-%m-%d').date().isoformat()
#         for day_data in data.get('details', []):
#             if 'date' in day_data and day_data['date']:
#                 day_data['date'] = datetime.strptime(day_data['date'], '%Y-%m-%d').date().isoformat()
#             if day_data.get('accommodation'):
#                 if 'arrival_date' in day_data['accommodation'] and day_data['accommodation']['arrival_date']:
#                     day_data['accommodation']['arrival_date'] = datetime.strptime(day_data['accommodation']['arrival_date'], '%Y-%m-%d').date().isoformat()
#                 if 'departure_date' in day_data['accommodation'] and day_data['accommodation']['departure_date']:
#                     day_data['accommodation']['departure_date'] = datetime.strptime(day_data['accommodation']['departure_date'], '%Y-%m-%d').date().isoformat()


#         response = requests.put(f"{FASTAPI_BASE_URL}/plans/{plan_id}", json=data)
#         response.raise_for_status() # 檢查 HTTP 請求是否成功

#         return jsonify({"status": "success", "plan": response}), 200

#     except requests.exceptions.RequestException as e:
#         if response.status_code == 404:
#             return jsonify({"status": "error", "message": "Plan not found"}), 404
#         if response.status_code == 400:
#             error_detail = response.json().get("detail", "未知錯誤")
#             return jsonify({"status": "error", "message": f"後端請求失敗: {error_detail}"}), 400
#         return jsonify({"status": "error", "message": f"無法連接後端服務或請求失敗: {e}"}), 500
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 400

@plan_bp.route("/plans/<int:plan_id>/status", methods=["PATCH"])
def update_plan_status(plan_id):
    """
    代理將計畫狀態更新請求轉發到 FastAPI 後端。
    """
    try:
        # 從請求體中獲取 JSON 數據
        request_data = request.get_json()
        if not request_data or 'status' not in request_data:
            return jsonify({"status": "error", "message": "請求體缺少 'status' 字段"}), 400

        # 向 FastAPI 後端發送 PATCH 請求
        response = requests.patch(
            f"{FASTAPI_BASE_URL}/plans/{plan_id}/status",
            json=request_data # 發送 JSON 數據
        )
        response.raise_for_status() # 檢查 HTTP 請求是否成功

        updated_plan = response.json()
        return jsonify({"status": "success", "plan": updated_plan}), 200

    except requests.exceptions.HTTPError as e:
        return jsonify({"status": "error", "message": f"後端服務返回錯誤: {e.response.status_code} - {e.response.text}"}), e.response.status_code
    except requests.exceptions.ConnectionError as e:
        return jsonify({"status": "error", "message": f"無法連接後端服務: {e}"}), 503
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"請求後端服務失敗: {e}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"服務內部錯誤: {str(e)}"}), 500


@plan_bp.route("/plans/<int:plan_id>", methods=["GET"])
def get_plan(plan_id):
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/plans/{plan_id}")
        response.raise_for_status() # 檢查 HTTP 請求是否成功
        plan_data = response.json()
        print(plan_data)
        if plan_data.get("status") == "draft": # 行程在草案階段
            return render_template("itinerary_planning.html", plan=plan_data)
        return render_template("plan.html", plan=plan_data)
    
    except requests.exceptions.RequestException as e:
        if response.status_code == 404:
            abort(404) # 如果計畫不存在，返回 404
        return jsonify({"status": "error", "message": f"無法連接後端服務或請求失敗: {e}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    
@plan_bp.route("/plans/", methods=["GET"])
def get_all_plans():
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/plans/")
        response.raise_for_status() # 檢查 HTTP 請求是否成功
        plans = response.json()
        return jsonify({"status": "success", "plans": plans}), 200
    
    except requests.exceptions.RequestException as e:
        if response.status_code == 404:
            abort(404) # 如果計畫不存在，返回 404
        return jsonify({"status": "error", "message": f"無法連接後端服務或請求失敗: {e}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@plan_bp.route("/plans/<int:plan_id>", methods=["DELETE"])
def delete_plan_route(plan_id):
    try:
        response = requests.delete(f"{FASTAPI_BASE_URL}/plans/{plan_id}")
        response.raise_for_status() # 檢查 HTTP 請求是否成功
        return jsonify({"status": "success", "message": f"Plan {plan_id} deleted successfully"}), 200
    
    except requests.exceptions.RequestException as e:
        if response.status_code == 404:
            return jsonify({"status": "error", "message": "Plan not found"}), 404
        return jsonify({"status": "error", "message": f"無法連接後端服務或請求失敗: {e}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
