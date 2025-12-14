from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, crud
from app.routes.auth import get_current_user
from app.models import Order

router = APIRouter(prefix="/orders", tags=["Orders"])


# --------------------------------------------------
#  CREATE ORDER
# --------------------------------------------------
@router.post("/", response_model=schemas.Order, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Tạo đơn hàng mới.
    - Kiểm tra xem danh sách item có rỗng không
    - Tự động kiểm tra tồn kho
    - Trừ tồn kho
    - Tạo bản ghi Order + OrderItems
    """
    if not order_data.items or len(order_data.items) == 0:
        raise HTTPException(
            status_code=400,
            detail="Đơn hàng phải có ít nhất 1 sản phẩm."
        )

    order = crud.create_order(db, current_user.user_id, order_data)
    return order


# --------------------------------------------------
#  GET ALL ORDERS
# --------------------------------------------------
@router.get("/", response_model=list[schemas.Order])
def list_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Lấy danh sách đơn hàng:
    - Admin → xem tất cả đơn
    - User → chỉ xem đơn họ tạo
    """
    if current_user.role.lower() == "admin":
        return crud.get_orders(db)

    return db.query(Order).filter(Order.created_by == current_user.user_id).all()


# --------------------------------------------------
#  GET ORDER BY ID
# --------------------------------------------------
@router.get("/{order_id}", response_model=schemas.Order)
def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Lấy chi tiết đơn hàng theo ID.
    - Admin → xem bất kỳ đơn
    - User → chỉ xem đơn họ tạo
    """
    order = crud.get_order(db, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng.")

    # Nếu không phải admin thì chỉ được xem đơn của mình
    if current_user.role.lower() != "admin":
        if order.created_by != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền xem đơn hàng này."
            )

    return order
