/**
 * 台灣市場常見廠牌 / 車型（新增車輛彈窗的點選方塊用）
 * - 自行整理，非任何網站資料；不在清單內的用「其他」手動輸入
 * - value 存英文廠牌名（與既有資料一致，例：'Toyota'、'BMW'），zh 只用於顯示
 * - 陣列順序 = 顯示順序：熱門廠牌在前
 */
export interface CatalogBrand {
  value: string;
  zh: string;
  models: string[];
}

export const CAR_BRANDS: CatalogBrand[] = [
  { value: 'Toyota', zh: '豐田', models: ['Altis', 'Corolla Cross', 'Yaris', 'Yaris Cross', 'Vios', 'Camry', 'RAV4', 'Prius', 'C-HR', 'Sienta', 'Sienna', 'Alphard', 'Town Ace', 'Hilux', 'Land Cruiser', 'Land Cruiser Prado', 'bZ4X', 'GR86', 'GR Supra', 'Corolla Sport', 'Wish'] },
  { value: 'Honda', zh: '本田', models: ['Fit', 'City', 'Civic', 'Civic Type R', 'Accord', 'HR-V', 'CR-V', 'ZR-V', 'Odyssey'] },
  { value: 'Nissan', zh: '日產', models: ['Sentra', 'Kicks', 'X-Trail', 'Tiida', 'Juke', 'Leaf', 'Livina', 'March', 'Altima', 'Teana', 'Z', 'GT-R', 'Navara'] },
  { value: 'Mitsubishi', zh: '三菱', models: ['Outlander', 'Eclipse Cross', 'Colt Plus', 'Grand Lancer', 'Lancer Fortis', 'Delica', 'ASX'] },
  { value: 'Mazda', zh: '馬自達', models: ['Mazda2', 'Mazda3', 'Mazda6', 'CX-3', 'CX-30', 'CX-5', 'CX-60', 'CX-9', 'MX-5', 'MX-30'] },
  { value: 'Ford', zh: '福特', models: ['Focus', 'Kuga', 'Mondeo', 'Fiesta', 'EcoSport', 'Escape', 'Ranger', 'Mustang', 'Mustang Mach-E', 'Tourneo Connect'] },
  { value: 'Hyundai', zh: '現代', models: ['Tucson', 'Tucson L', 'Santa Fe', 'Custin', 'Venue', 'Kona', 'Elantra', 'Ioniq 5', 'Ioniq 6', 'Staria'] },
  { value: 'Lexus', zh: '凌志', models: ['LBX', 'UX', 'NX', 'RX', 'LX', 'ES', 'IS', 'LS', 'RC', 'LC', 'LM', 'RZ', 'CT'] },
  { value: 'Mercedes-Benz', zh: '賓士', models: ['A-Class', 'B-Class', 'C-Class', 'E-Class', 'S-Class', 'CLA', 'CLE', 'GLA', 'GLB', 'GLC', 'GLE', 'GLS', 'G-Class', 'EQA', 'EQB', 'EQE', 'EQS', 'V-Class', 'SL', 'AMG GT'] },
  { value: 'BMW', zh: '寶馬', models: ['1系列', '2系列', '3系列', '4系列', '5系列', '7系列', '8系列', 'X1', 'X2', 'X3', 'X4', 'X5', 'X6', 'X7', 'Z4', 'i3', 'i4', 'i5', 'i7', 'iX', 'iX1', 'iX3', 'M2', 'M3', 'M4'] },
  { value: 'Volkswagen', zh: '福斯', models: ['Polo', 'Golf', 'Golf GTI', 'Golf Variant', 'T-Cross', 'T-Roc', 'Tiguan', 'Tiguan Allspace', 'Touran', 'Passat', 'Arteon', 'ID.4', 'Caddy', 'Multivan', 'Transporter'] },
  { value: 'Tesla', zh: '特斯拉', models: ['Model 3', 'Model Y', 'Model S', 'Model X'] },
  { value: 'Audi', zh: '奧迪', models: ['A1', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'Q2', 'Q3', 'Q5', 'Q7', 'Q8', 'Q4 e-tron', 'Q8 e-tron', 'e-tron GT', 'TT', 'R8'] },
  { value: 'Subaru', zh: '速霸陸', models: ['Impreza', 'XV', 'Crosstrek', 'Forester', 'Outback', 'Levorg', 'WRX', 'BRZ', 'Solterra'] },
  { value: 'Suzuki', zh: '鈴木', models: ['Swift', 'Vitara', 'S-Cross', 'Jimny', 'Ignis', 'Baleno', 'SX4'] },
  { value: 'Kia', zh: '起亞', models: ['Picanto', 'Stonic', 'Sportage', 'Sorento', 'Carnival', 'Niro', 'EV6', 'EV9'] },
  { value: 'Luxgen', zh: '納智捷', models: ['n7', 'U6', 'URX', 'S5', 'U5', 'M7', 'V7'] },
  { value: 'Volvo', zh: '富豪', models: ['XC40', 'XC60', 'XC90', 'S60', 'S90', 'V60', 'V90', 'EX30', 'EX40', 'C40'] },
  { value: 'Porsche', zh: '保時捷', models: ['911', '718', 'Macan', 'Cayenne', 'Panamera', 'Taycan'] },
  { value: 'MINI', zh: 'MINI', models: ['Cooper 3門', 'Cooper 5門', 'Clubman', 'Countryman', 'Cabrio', 'Aceman'] },
  { value: 'Skoda', zh: '斯柯達', models: ['Fabia', 'Scala', 'Kamiq', 'Karoq', 'Kodiaq', 'Octavia', 'Superb', 'Enyaq'] },
  { value: 'Peugeot', zh: '寶獅', models: ['208', '2008', '308', '3008', '408', '508', '5008', 'Rifter'] },
  { value: 'Citroen', zh: '雪鐵龍', models: ['C3', 'C3 Aircross', 'C4', 'C5 Aircross', 'C5 X', 'Berlingo'] },
  { value: 'Infiniti', zh: '極致', models: ['Q50', 'Q60', 'QX50', 'QX55', 'QX60'] },
  { value: 'CMC', zh: '中華', models: ['Veryca 菱利', 'Zinger', 'J Space'] },
  { value: 'Land Rover', zh: '荒原路華', models: ['Defender', 'Discovery', 'Discovery Sport', 'Range Rover', 'Range Rover Sport', 'Range Rover Velar', 'Range Rover Evoque'] },
  { value: 'Jaguar', zh: '捷豹', models: ['E-Pace', 'F-Pace', 'I-Pace', 'XE', 'XF', 'F-Type'] },
  { value: 'Jeep', zh: '吉普', models: ['Renegade', 'Compass', 'Cherokee', 'Grand Cherokee', 'Wrangler', 'Gladiator'] },
  { value: 'MG', zh: 'MG', models: ['HS', 'ZS', 'MG4'] },
  { value: 'Maserati', zh: '瑪莎拉蒂', models: ['Ghibli', 'Quattroporte', 'Levante', 'Grecale', 'MC20'] },
  { value: 'Alfa Romeo', zh: '愛快羅密歐', models: ['Giulia', 'Stelvio', 'Tonale'] },
  { value: 'Ferrari', zh: '法拉利', models: ['296', 'Roma', 'SF90', '812', 'Purosangue'] },
  { value: 'Lamborghini', zh: '藍寶堅尼', models: ['Huracan', 'Urus', 'Revuelto'] },
  { value: 'Bentley', zh: '賓利', models: ['Bentayga', 'Continental GT', 'Flying Spur'] },
  { value: 'Rolls-Royce', zh: '勞斯萊斯', models: ['Ghost', 'Phantom', 'Cullinan', 'Spectre'] },
  { value: 'Lotus', zh: '蓮花', models: ['Emira', 'Eletre'] },
  { value: 'Isuzu', zh: '五十鈴', models: ['Elf', 'D-Max'] },
  { value: 'Hino', zh: '日野', models: ['300系列', '500系列'] },
];

export const MOTO_BRANDS: CatalogBrand[] = [
  { value: 'Kymco', zh: '光陽', models: ['Many', 'Like', 'GP', '雷霆S', 'KRV', 'Nice', '新名流', 'AK550', 'Ionex'] },
  { value: 'SYM', zh: '三陽', models: ['JET SL', 'DRG', '4MICA', 'Woo', 'CLBCU', '迪爵', 'FNX', 'MMBCU'] },
  { value: 'Yamaha', zh: '山葉', models: ['勁戰', 'BWS', 'Force', 'AUGUR', 'RS Neo', 'Limi', 'XMAX', 'TMAX', 'MT-03', 'MT-07', 'YZF-R3', 'YZF-R15'] },
  { value: 'Gogoro', zh: '睿能', models: ['Gogoro S', 'Gogoro VIVA', 'Gogoro CrossOver', 'Gogoro JEGO', 'Gogoro Delight', 'Gogoro SuperSport'] },
  { value: 'Suzuki', zh: '台鈴', models: ['Swish', 'Saluto', 'GSX-R150', 'GSX-S150', 'SV650'] },
  { value: 'Aeon', zh: '宏佳騰', models: ['Ai-1', 'Ai-2', 'Ai-3', 'Ai-4'] },
  { value: 'PGO', zh: '摩特動力', models: ['Tigra', 'J-BUBU', 'Ur1'] },
  { value: 'Honda', zh: '本田', models: ['CB650R', 'Rebel 500', 'Forza', 'ADV', 'CBR500R'] },
  { value: 'Kawasaki', zh: '川崎', models: ['Ninja 400', 'Ninja 650', 'Z400', 'Z650', 'Z900', 'Versys 650'] },
  { value: 'Vespa', zh: '偉士牌', models: ['Primavera', 'Sprint', 'GTS'] },
  { value: 'Harley-Davidson', zh: '哈雷', models: ['Sportster S', 'Nightster', 'Street Glide', 'Fat Boy'] },
  { value: 'Ducati', zh: '杜卡迪', models: ['Monster', 'Scrambler', 'Panigale', 'Multistrada'] },
  { value: 'Triumph', zh: '凱旋', models: ['Speed 400', 'Trident 660', 'Street Triple', 'Bonneville'] },
  { value: 'BMW', zh: '寶馬', models: ['G 310 R', 'R 1250 GS', 'S 1000 RR', 'C 400 X'] },
];

/** 依「車輛型式」決定用汽車還是機車清單 */
export function brandsFor(vehicleType: string | null | undefined): CatalogBrand[] {
  return vehicleType && vehicleType.includes('機車') ? MOTO_BRANDS : CAR_BRANDS;
}

/** 找既有值對應的廠牌（大小寫不分，舊資料可能是 'toyota'） */
export function findBrand(list: CatalogBrand[], value: string | null | undefined): CatalogBrand | undefined {
  if (!value) return undefined;
  const v = value.trim().toLowerCase();
  return list.find((b) => b.value.toLowerCase() === v || b.zh === value.trim());
}
