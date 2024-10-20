import BestSellerProducts from "./BestSellerProducts/BestSellerProducts";
import Brands from "./Brands/Brands";
import CategoryBanner from "./CategoryBanner/CategoryBanner";
import DiscountBanner from "./DiscountBanner/DiscountBanner";
import HeroSlider from "./HeroSlider/HeroSlider";
import NewProducts from "./NewProducts/NewProducts";

const HomePage = () => {
  return (
    <>
      <main className="z-[2] bg-white">
        <HeroSlider />
        <CategoryBanner />
        <NewProducts />
        <DiscountBanner />
        <BestSellerProducts />
        <Brands />
      </main>
    </>
  );
};

export default HomePage;
