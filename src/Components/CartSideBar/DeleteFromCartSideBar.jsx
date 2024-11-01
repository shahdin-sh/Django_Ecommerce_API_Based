import { IoClose } from "react-icons/io5";
import { useDispatch } from "react-redux";
import { DeleteFromCart } from "../../Redux_Toolkit/Cart/DeleteFromCart";

const DeleteFromCartSideBar = ({ ID, setReRender, reRender }) => {
  const dispatch = useDispatch();
  const handleDelete = () => {
    dispatch(DeleteFromCart(ID));
    setReRender(!reRender);
  };
  return (
    <>
      <button onClick={handleDelete} className="w-[20px] h-[20px]">
        <IoClose />
      </button>
    </>
  );
};

export default DeleteFromCartSideBar;
