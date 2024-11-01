import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { getCategory } from "../../Redux_Toolkit/Categoties/CategorySlice";

const CategoryLink = ({ category }) => {
  const { categoryData, loading, error } = useSelector((state) => state.categoryData);
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(getCategory(category));
  }, []);

  if (!categoryData) {
    return loading ? <p>loading...</p> : "";
  }

  return (
    <>
      <p className="text-[16px] font-[main] text-[rgb(17,17,17)] mb-[20px]">
        دسته بندی: <span className="text-[rgb(102,102,102)]">{categoryData.title}</span>
      </p>
    </>
  );
};

export default CategoryLink;
