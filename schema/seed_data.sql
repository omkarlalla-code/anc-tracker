-- Test data (encrypted fields are placeholder blobs — not real ciphertext)
INSERT INTO patients VALUES
('P001', cast('encrypted_name_1'  as blob), cast('encrypted_phone_1'  as blob), 24, 'Kalyani',    '2024-01-15', '2024-01-10', 1, CURRENT_TIMESTAMP),
('P002', cast('encrypted_name_2'  as blob), cast('encrypted_phone_2'  as blob), 28, 'Pune Rural', '2024-01-20', '2024-01-15', 1, CURRENT_TIMESTAMP);

INSERT INTO visits VALUES
(1, 'P001', 1, 'First contact',  '2024-01-17', NULL,         'pending',   NULL),
(2, 'P001', 2, 'Second contact', '2024-05-29', NULL,         'pending',   NULL),
(3, 'P002', 1, 'First contact',  '2024-01-22', '2024-01-22', 'completed', 'Normal baseline');
